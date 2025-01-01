from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from order.models import Order
from user.models import Account
# import sslcommerz_lib
from sslcommerz_lib import SSLCOMMERZ
from django.conf import settings
import logging
from django.http import JsonResponse
from django.conf import settings
import logging


logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
def initiate_payment(request):
    order_id = request.data.get('order_id')
    user = request.user

    if not user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        account = Account.objects.get(user=user)
        order = Order.objects.get(id=order_id, user=account)
    except Account.DoesNotExist:
        logger.error(f"No associated Account found for user {user.username}")
        return Response({'error': 'User does not have an associated account'}, status=status.HTTP_400_BAD_REQUEST)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for user {user.username}")
        return Response({'error': 'Order does not exist'}, status=status.HTTP_404_NOT_FOUND)


    payment_data = {
        'total_amount': str(order.total_amount),
        'currency': 'BDT',
        'tran_id': order.transaction_id,  # Use the order's transaction ID
        # 'tran_id':unique_transaction_id_generator(),
        'success_url': settings.SSLCOMMERZ['SUCCESS_URL'],
        'fail_url': settings.SSLCOMMERZ['FAIL_URL'],
        'cancel_url': settings.SSLCOMMERZ['CANCEL_URL'],
        'cus_name': user.username,
        'cus_email': user.email,
        'cus_phone': getattr(user, 'phone', 'N/A'),
        'cus_add1': 'Customer Address',
        'cus_city': 'Dhaka',
        'cus_country': 'Bangladesh',
        'shipping_method': 'NO',
        'product_name': 'Flower Order',
        'product_category': 'Flower',
        'product_profile': 'general',
    }

    sslcz = SSLCOMMERZ({
        'store_id': settings.SSLCOMMERZ['STORE_ID'],
        'store_pass': settings.SSLCOMMERZ['STORE_PASSWORD'],
        'issandbox': settings.SSLCOMMERZ['IS_SANDBOX']
    })

    response = sslcz.createSession(payment_data)

    if response.get('status') == 'SUCCESS':
        logger.info(f"Payment session created for order {order_id}: {response['GatewayPageURL']}")
        return Response({'payment_url': response['GatewayPageURL']}, status=status.HTTP_200_OK)
    else:
        logger.error(f"Failed to create payment session for order {order_id}: {response}")
        return Response({'error': 'Failed to create payment session'}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def update_order_status(order, status, val_id=None):
    if order.payment_status in ['Completed', 'Failed']:
        logger.warning(f"Order {order.id} already processed. Current status: {order.payment_status}")
        return
    
    order.payment_status = status
    if val_id:
        order.transaction_id = val_id
    order.status = 'Paid' if status == 'Completed' else 'Failed'
    order.save()



logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
def payment_success(request):
    tran_id = request.data.get('tran_id')
    val_id = request.data.get('val_id')
    logger.info(f"Received payment success data: {request.data}")
    if not tran_id or not val_id:
        logger.error("Missing transaction ID or validation ID in the request.")
        return Response({'error': 'Missing transaction or validation ID'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        order = Order.objects.get(transaction_id=tran_id)
    except Order.DoesNotExist:
        logger.error(f"Order with transaction ID {tran_id} not found.")
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    sslcz = SSLCOMMERZ({
        'store_id': settings.SSLCOMMERZ['STORE_ID'],
        'store_pass': settings.SSLCOMMERZ['STORE_PASSWORD'],
        'issandbox': settings.SSLCOMMERZ['IS_SANDBOX']
    })
    response = sslcz.validationTransactionOrder(val_id)
    logger.info(f"Validation response from SSLCOMMERZ: {response}")
    if response.get('status') == 'VALID':
        order.payment_status = 'Paid'
        order.save()
        logger.info(f"Payment successful for order {order.id}.")
        return Response({'message': 'Payment verified and order updated'}, status=status.HTTP_200_OK)
    else:
        logger.error(f"Payment validation failed: {response}")
        return Response({'error': 'Payment validation failed', 'details': response}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
def payment_fail(request):
    data = request.GET if request.method == 'GET' else request.POST

    transaction_id = data.get('tran_id')
    status = data.get('status')

    if status == 'FAILED':
        try:
            order = Order.objects.get(transaction_id=transaction_id)
            order.payment_status = 'Failed'
            order.order_status = 'Cancelled'
            order.save()
            return JsonResponse({'message': 'Order payment failed and status updated successfully.'})
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found for this transaction ID.'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid payment status.'}, status=400)

@csrf_exempt
@api_view(['POST'])
def payment_cancel(request):
    tran_id = request.data.get('tran_id')

    if not tran_id:
        logger.error("Missing transaction ID in payment cancelation")
        return Response({'error': 'Missing transaction ID'}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Payment canceled for transaction ID: {tran_id}")
    return Response({'message': 'Payment Cancelled'}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def payment_ipn(request):
    data = request.data
    tran_id = data.get('tran_id')
    val_id = data.get('val_id')
    status = data.get('status')

    if not tran_id or not status:
        logger.error(f"Missing required IPN data: tran_id={tran_id}, status={status}")
        return Response({'error': 'Missing required IPN data'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        order_id = tran_id.split("_")[1]
        order = Order.objects.get(id=order_id)

        if status == 'VALID':
            update_order_status(order, 'Completed', val_id)
            logger.info(f"IPN validated for order {order_id}, transaction ID: {val_id}")
            return Response({'message': 'Payment validated successfully'}, status=status.HTTP_200_OK)
        else:
            update_order_status(order, 'Failed')
            logger.warning(f"IPN validation failed for order {order_id}, status: {status}")
            return Response({'error': 'Payment validation failed'}, status=status.HTTP_400_BAD_REQUEST)
    except Order.DoesNotExist:
        logger.error(f"Order not found for IPN transaction ID {tran_id}")
        return Response({'error': 'Order does not exist'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error processing IPN: {str(e)}", exc_info=True)
        return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
