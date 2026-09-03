"""Amazon Multi-Channel Fulfillment (MCF) Integration using SP-API.

This module uses python-amazon-sp-api to communicate with Amazon's 
FulfillmentOutbound API to dispatch orders and retrieve tracking information.
"""
import logging
from django.conf import settings
from sp_api.api import FulfillmentOutbound
from sp_api.base import SellingApiException, Marketplaces

logger = logging.getLogger(__name__)


def is_configured():
    # AWS IAM credentials are no longer required by SP-API (retired Oct 2023);
    # only the LWA refresh token and app credentials are needed.
    return bool(
        settings.AMAZON_SP_API_REFRESH_TOKEN and
        settings.AMAZON_SP_API_LWA_CLIENT_ID and
        settings.AMAZON_SP_API_LWA_CLIENT_SECRET
    )


def _get_credentials():
    return {
        'refresh_token': settings.AMAZON_SP_API_REFRESH_TOKEN,
        'lwa_app_id': settings.AMAZON_SP_API_LWA_CLIENT_ID,
        'lwa_client_secret': settings.AMAZON_SP_API_LWA_CLIENT_SECRET,
    }


def create_fulfillment_order(order):
    """Submits an order to Amazon MCF for fulfillment."""
    if not is_configured():
        logger.warning('Amazon MCF is not configured. Skipping fulfillment for order %s', order.order_number)
        return False

    try:
        # We use AE marketplace (United Arab Emirates)
        api = FulfillmentOutbound(
            credentials=_get_credentials(),
            marketplace=Marketplaces.AE
        )

        items = []
        for item in order.items.all():
            items.append({
                'sellerSku': item.variant.sku if item.variant else 'N/A',
                'sellerFulfillmentOrderItemId': str(item.id),
                'quantity': item.quantity,
                'displayableComment': 'Elvessora Perfumes Order'
            })

        payload = {
            'marketplaceId': Marketplaces.AE.marketplace_id,
            'sellerFulfillmentOrderId': order.order_number,
            'displayableOrderId': order.order_number,
            'displayableOrderDate': order.created_at.isoformat(),
            'displayableOrderComment': 'Thank you for your order with Elvessora Perfumes',
            'shippingSpeedCategory': 'Standard',
            'destinationAddress': {
                'name': order.shipping_name,
                'addressLine1': order.shipping_address[:50],
                'city': order.shipping_city,
                'stateOrRegion': order.shipping_state,
                'postalCode': order.shipping_pincode or '00000',
                'countryCode': 'AE',
                'phone': order.shipping_phone or '0000000000'
            },
            'items': items
        }

        response = api.create_fulfillment_order(**payload)
        logger.info('Successfully sent order %s to Amazon MCF.', order.order_number)
        
        order.amazon_fulfillment_status = 'Submitted'
        order.save()
        return True

    except SellingApiException as e:
        logger.error('Failed to send order %s to Amazon MCF: %s', order.order_number, e)
        return False
    except Exception as e:
        logger.exception('Unexpected error sending order %s to Amazon MCF: %s', order.order_number, e)
        return False


def get_fulfillment_order(order_number):
    """Retrieves the status of an MCF order."""
    if not is_configured():
        return None

    try:
        api = FulfillmentOutbound(
            credentials=_get_credentials(),
            marketplace=Marketplaces.AE
        )
        response = api.get_fulfillment_order(order_number)
        return response.payload
    except SellingApiException as e:
        logger.error('Failed to get Amazon MCF status for %s: %s', order_number, e)
        return None
