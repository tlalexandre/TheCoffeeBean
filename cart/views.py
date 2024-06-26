from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from orderonline.models import (
    MenuItem, MenuItemIngredient, MenuItemIncludedItem
)
from orderonline.forms import AddToCartForm
from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F


def cart(request):
    ''' A view to return the cart page'''
    cart = request.session.get('cart', [])
    cart_total_price = get_cart_total_price(cart)

    # Calculate subtotal for each item in the cart
    for item in cart:
        item['subtotal'] = float(item['price']) * item['quantity']

    # Render the cart template
    return render(
        request,
        'cart/cart.html',
        {'cart': cart, 'cart_total_price': cart_total_price})


def price_header(request):
    ''' Get the cart total price '''
    cart_total_price = get_cart_total_price(request)

    # Render some other template and pass the cart total price
    return render(request, 'base.html', {'cart_total_price': cart_total_price})


class DecimalEncoder(DjangoJSONEncoder):
    ''' A custom JSON encoder to handle Decimal objects'''

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def is_int(value):
    ''' Check if a value is an integer'''
    try:
        int(value)
        return True
    except ValueError:
        return False


def get_cart_total_price(cart):
    ''' Calculate the total price of the cart'''
    cart_total_price = Decimal(0)
    for item_data in cart:
        item_price = Decimal(item_data.get('price', 0))
        # Get the quantity, default to 1 if not provided
        item_quantity = item_data.get('quantity', 1)
        # Calculate the total price for this item
        item_total_price = item_price * item_quantity
        cart_total_price += item_total_price
    return cart_total_price


def calculate_total_price(
        request,
        item,
        selected_options,
        selected_extras,
        selected_included_options,
        selected_included_extras,
        quantity
):
    ''' Calculate the total price and subtotal for an item'''
    total_price = Decimal(item.price)
    for option_id in selected_options:
        option = get_object_or_404(MenuItemIngredient, id=int(option_id))
        total_price += Decimal(option.price)
    for extra_id in selected_extras:
        extra = get_object_or_404(MenuItemIngredient, id=int(extra_id))
        total_price += Decimal(extra.price)
    included_item_id = request.POST.get('included_item')
    if included_item_id:
        included_item = get_object_or_404(
            MenuItemIncludedItem, id=int(included_item_id))
        total_price += Decimal(included_item.price)
        for option_id in selected_included_options:
            option = get_object_or_404(MenuItemIngredient, id=int(option_id))
            total_price += Decimal(option.price)
        for extra_id in selected_included_extras:
            extra = get_object_or_404(MenuItemIngredient, id=int(extra_id))
            total_price += Decimal(extra.price)
    subtotal = total_price * quantity
    return total_price, subtotal


def add_to_cart(request):
    ''' Add an item to the cart'''
    if request.method == 'POST':
        # Get the selected item
        item_id = request.POST.get('item_id')
        item = get_object_or_404(MenuItem, id=item_id)
        quantity = int(request.POST.get('quantity', 1))

        # Get the selected included item
        included_item_id = request.POST.get('included_item')
        included_item = None
        if included_item_id:
            included_item = get_object_or_404(
                MenuItemIncludedItem, id=included_item_id)

        # Get the selected options and extras
        selected_options = []
        selected_extras = []
        selected_included_options = []
        selected_included_extras = []

        for key, values in request.POST.lists():
            if 'included_item_option_' in key:
                selected_included_options.extend(values)
            elif 'included_item_extra_' in key:
                selected_included_extras.extend(values)
            elif 'Extras' in key:
                selected_extras.extend(values)
            else:
                for value in values:
                    if is_int(value) and MenuItemIngredient.objects.filter(
                        id=int(value),
                        option__isnull=False,
                        menu_item=item
                    ).exists():
                        selected_options.extend([value])

        try:
            total_price, subtotal = calculate_total_price(
                request,
                item,
                selected_options,
                selected_extras,
                selected_included_options,
                selected_included_extras,
                quantity
            )
            cart_item = {
                'id': item.id,
                'name': item.name,
                'quantity': quantity,
                'original_price': "{:.2f}".format(float(item.price)),
                'price': "{:.2f}".format(float(total_price)),
                'subtotal': "{:.2f}".format(float(subtotal)),
                'options': [
                    {
                        'id': int(option_id),
                        'name': MenuItemIngredient.objects.get(
                            id=int(option_id)
                        ).ingredient.name,
                        'price': "{:.2f}".format(
                            float(
                                MenuItemIngredient.objects.get(
                                    id=int(option_id)).price)
                        )
                    }
                    for option_id in selected_options
                    if is_int(option_id) and
                    MenuItemIngredient.objects.filter(
                        id=int(option_id)
                    ).exists()
                ],
                'extras': [
                    {
                        'id': int(extra_id),
                        'name': MenuItemIngredient.objects.get(
                            id=int(extra_id)
                        ).ingredient.name,
                        'price': "{:.2f}".format(
                            float(
                                MenuItemIngredient.objects.get(
                                    id=int(extra_id)).price)
                        )
                    }
                    for extra_id in selected_extras
                    if is_int(extra_id) and
                    MenuItemIngredient.objects.filter(
                        id=int(extra_id)
                    ).exists()
                ],
                'image_url': item.image.url if item.image else None,
            }
            if included_item is not None:
                cart_item['included_item'] = {
                    'id': included_item.included_item.id,
                    'name': included_item.included_item.name,
                    'price': "{:.2f}".format(float(included_item.price)),
                    'options': [
                        {
                            'id': int(option_id),
                            'name': MenuItemIngredient.objects.get(
                                id=int(option_id)
                            ).ingredient.name,
                            'price': "{:.2f}".format(
                                float(
                                    MenuItemIngredient.objects.get(
                                        id=int(option_id)
                                    ).price
                                )
                            )
                        }
                        for option_id in selected_included_options
                        if is_int(option_id) and
                        MenuItemIngredient.objects.filter(
                            id=int(option_id)
                        ).exists()
                    ],
                    'extras': [
                        {
                            'id': int(extra_id),
                            'name': MenuItemIngredient.objects.get(
                                id=int(extra_id)
                            ).ingredient.name,
                            'price': "{:.2f}".format(
                                float(
                                    MenuItemIngredient.objects.get(
                                        id=int(extra_id)
                                    ).price
                                )
                            )
                        }
                        for extra_id in selected_included_extras
                        if is_int(extra_id) and
                        MenuItemIngredient.objects.filter(
                            id=int(extra_id)
                        ).exists()
                    ],
                }
        except MenuItemIngredient.DoesNotExist as e:
            error_message = (
                'An error occurred while adding the item to the cart. '
                'Please try again.'
            )
            messages.error(
                request,
                error_message)
            return redirect('cart')

        # Get the cart from the session
        cart = request.session.get('cart', [])

        # Add the new item to the cart
        if 'quantity' not in cart_item:
            cart_item['quantity'] = 1
        cart.append(cart_item)

        # Save the cart in the session
        request.session['cart'] = cart

        # Display a success message
        messages.success(request, f'{item.name} has been added to cart')

        return redirect('order_online')


def delete_from_cart(request, item_index):
    ''' Delete an item from the cart'''
    cart = request.session.get('cart', [])

    # Check if the item index is valid
    if 0 <= item_index < len(cart):
        # Remove the item at the given index from the cart
        del cart[item_index]

        # Save the cart back to the session
        request.session['cart'] = cart

        # Display a success message
        messages.success(request, 'Item has been removed from cart')

    return redirect('cart')


def update_cart_item(request, item_index):
    ''' Update an item in the cart'''
    cart = request.session.get('cart', [])

    # Check if the item index is valid
    if 0 <= item_index < len(cart):
        # Get the item at the given index from the cart
        cart_item = cart[item_index]

        # Convert the cart item back to a MenuItem instance
        item = MenuItem.objects.get(name=cart_item['name'])
        
        if request.method == 'POST':

            # Get the selected options and extras
            selected_options = []
            selected_extras = []
            selected_included_options = []
            selected_included_extras = []

            # Get the quantity from the POST data, default to 1 if not provided
            quantity = int(request.POST.get('quantity', 1))

            # Get the selected included item
            included_item_id = request.POST.get('included_item')
            included_item = None
            if included_item_id:
                included_item = get_object_or_404(
                    MenuItemIncludedItem, id=included_item_id)

            # Get the selected options and extras
            selected_options = request.POST.getlist('options', [])
            selected_extras = request.POST.getlist('extras', [])
            selected_included_options = request.POST.getlist(
                'included_options', [])
            selected_included_extras = request.POST.getlist(
                'included_extras', [])

            for key, values in request.POST.lists():
                if 'included_item_option_' in key:
                    selected_included_options.extend(values)
                elif 'included_item_extra_' in key:
                    selected_included_extras.extend(values)
                elif 'Extras' in key:
                    for value in values:
                        if (is_int(value) and
                                MenuItemIngredient.objects.filter(
                                    id=int(value),
                                    option__isnull=True,
                                    menu_item=item
                        ).exists()):
                            # Use append instead of extend
                            selected_extras.append(value)
                else:
                    for value in values:
                        if (is_int(value) and
                                MenuItemIngredient.objects.filter(
                                    id=int(value),
                                    option__isnull=False,
                                    menu_item=item
                        ).exists()):
                            # Use append instead of extend
                            selected_options.append(value)

            try:
                # Update the cart item
                total_price, _ = calculate_total_price(
                    request, item, selected_options, selected_extras,
                    selected_included_options, selected_included_extras,
                    quantity
                )
                cart_item['price'] = "{:.2f}".format(float(total_price))
                cart_item['options'] = [
                    {
                        'id': int(option_id),
                        'name': get_object_or_404(
                            MenuItemIngredient, id=int(option_id)
                        ).ingredient.name,
                        'price': "{:.2f}".format(
                            float(get_object_or_404(
                                MenuItemIngredient, id=int(option_id)
                            ).price)
                        )
                    }
                    for option_id in selected_options
                    if is_int(option_id) and
                    MenuItemIngredient.objects.filter(
                        id=int(option_id)
                    ).exists()
                ]
                cart_item['extras'] = [
                    {
                        'id': int(extra_id),
                        'name': get_object_or_404(
                            MenuItemIngredient, id=int(extra_id)
                        ).ingredient.name,
                        'price': "{:.2f}".format(
                            float(get_object_or_404(
                                MenuItemIngredient, id=int(extra_id)
                            ).price)
                        )
                    }
                    for extra_id in selected_extras
                    if is_int(extra_id) and
                    MenuItemIngredient.objects.filter(
                        id=int(extra_id)
                    ).exists()
                ]
                cart_item['quantity'] = quantity

                if included_item is not None:
                    cart_item['included_item'] = {
                        'id': included_item.included_item.id,
                        'name': included_item.included_item.name,
                        'price': "{:.2f}".format(float(included_item.price)),
                        'options': [
                            {
                                'name': MenuItemIngredient.objects.get(
                                    id=int(option_id)
                                ).ingredient.name,
                                'price': "{:.2f}".format(
                                    float(MenuItemIngredient.objects.get(
                                        id=int(option_id)
                                    ).price)
                                )
                            }
                            for option_id in selected_included_options
                            if is_int(option_id) and
                            MenuItemIngredient.objects.filter(
                                id=int(option_id)
                            ).exists()
                        ],
                        'extras': [
                            {
                                'name': MenuItemIngredient.objects.get(
                                    id=int(extra_id)
                                ).ingredient.name,
                                'price': "{:.2f}".format(
                                    float(MenuItemIngredient.objects.get(
                                        id=int(extra_id)
                                    ).price)
                                )
                            }
                            for extra_id in selected_included_extras
                            if is_int(extra_id) and
                            MenuItemIngredient.objects.filter(
                                id=int(extra_id)
                            ).exists()
                        ],
                    }
            except Exception as e:
                print("An error occurred: ", str(e))

            # Save the cart back to the session
            request.session['cart'] = cart

            # Display a success message
            messages.success(request, f'{item.name} has been updated')

            return redirect('cart')

        initial_data = {
            'item_id': item.id,
            'quantity': cart_item['quantity'],
        }

        included_items = MenuItemIncludedItem.objects.none()

        if 'included_item' in cart_item:
            included_items = MenuItemIncludedItem.objects.filter(
                included_item__name=cart_item['included_item']['name'])
            for included_item in included_items:
                initial_data['included_item'] = str(included_item.id)

        for option in cart_item['options']:
            menu_item_ingredients = MenuItemIngredient.objects.filter(
                ingredient__name=option['name'])
            initial_data[menu_item_ingredients.first().option.name] = [
                str(mii.id) for mii in menu_item_ingredients]

        # Initialize the list of IDs for the extras
        initial_data['Extras'] = []

        for extra in cart_item['extras']:
            menu_item_ingredients = MenuItemIngredient.objects.filter(
                ingredient__name=extra['name'])
            initial_data['Extras'].extend(
                [str(mii.id) for mii in menu_item_ingredients])

        form = AddToCartForm(initial=initial_data, item=item, adding=False)

        item_price = item.price
        for option in cart_item['options']:
            item_price += Decimal(option['price'])
        for extra in cart_item['extras']:
            item_price += Decimal(extra['price'])

        # Get the optionsExtras data
        optionsExtras = {}
        for included_item in MenuItemIncludedItem.objects.filter(menu_item=item):
            menu_item_ingredients = MenuItemIngredient.objects.filter(
                menu_item=included_item.included_item
            ).annotate(option_name=F('option__name')).values(
                'id', 'ingredient__name', 'option_name', 'price'
            )
            optionsExtras[included_item.id] = {'Extras': [], 'Options': {}}
            for menu_item_ingredient in menu_item_ingredients:
                option_name = menu_item_ingredient['option_name']
                included_id = included_item.id
                if option_name:
                    if option_name not in optionsExtras[included_id]['Options']:
                        optionsExtras[included_id]['Options'][option_name] = []
                    optionsExtras[included_id]['Options'][option_name].append(
                        menu_item_ingredient)
                else:
                    extras = optionsExtras[included_id]['Extras']
                    extras.append(menu_item_ingredient)

        optionsExtras_json = json.dumps(optionsExtras, cls=DecimalEncoder)

        # Pass the optionsExtras data to the template
        return render(
            request,
            'orderonline/update_item.html',
            {
                'form': form,
                'item_index': item_index,
                'item': item,
                'item_price': item_price,
                'optionsExtras': optionsExtras_json,
            }
        )
