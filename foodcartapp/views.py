from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from phonenumber_field.phonenumber import to_python

from .models import Product, Order, OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    order_data = request.data    
    errors = {}

    fields = ['firstname', 'lastname', 'address', 'phonenumber']
    
    for field in fields:
        if field not in order_data:
            errors[field] = 'Обязательное поле.'
            continue
            
        value = order_data[field]
        
        if value is None or value == '':
            errors[field] = 'Это поле не может быть пустым.'
            continue
            
        if not isinstance(value, str):
            errors[field] = 'Not a valid string.'
            continue

        if field == 'phonenumber':
            phone = to_python(value)
            if not phone or not phone.is_valid():
                errors['phonenumber'] = 'Введен некорректный номер телефона.'

    if 'products' not in order_data:
        errors['products'] = 'Обязательное поле.'
    else:
        products = order_data['products']
        if products is None:
            errors['products'] = 'Это поле не может быть пустым.'
        elif not isinstance(products, list):
            errors['products'] = f'Ожидался list со значениями, но был получен "{type(products).__name__}".'
        elif not products:
            errors['products'] = 'Этот список не может быть пустым.'
        else:
            for item in products:
                if not isinstance(item, dict) or 'product' not in item:
                    errors['products'] = 'Некорректная структура элемента списка.'
                    break
                
                product_id = item['product']
                try:
                    Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    errors['products'] = f'Недопустимый первичный ключ "{product_id}"'
                    break

    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    order = Order.objects.create(
        firstname=order_data['firstname'],
        lastname=order_data['lastname'],
        phonenumber=order_data['phonenumber'],
        address=order_data['address']
    )

    for item in order_data['products']:
        product = Product.objects.get(id=item['product'])
            
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item['quantity']
        )
        
    return JsonResponse({}, status=200)
