from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order
from .forms import OrderForm, OrderStatusForm, OrderItemFormSet
from accounts.utils import get_user_role


@login_required
def order_list(request):
    user_role = get_user_role(request.user)
    if user_role == 'guest':
        messages.error(request, 'У вас нет доступа к заказам.')
        return redirect('products:product_list')

    if user_role in ('admin', 'manager'):
        orders = Order.objects.select_related('customer', 'status', 'pickup_point').all()
    else:
        orders = Order.objects.select_related('customer', 'status', 'pickup_point').filter(
            customer=request.user
        )

    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'user_role': user_role,
    })


@login_required
def order_create(request):
    user_role = get_user_role(request.user)
    if user_role not in ('admin', 'client'):
        messages.error(request, 'У вас нет прав для создания заказа.')
        return redirect('orders:order_list')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.save()
            formset.instance = order
            formset.save()
            messages.success(request, 'Заказ успешно создан.')
            return redirect('orders:order_list')
    else:
        form = OrderForm()
        formset = OrderItemFormSet()

    return render(request, 'orders/order_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Создать заказ',
        'user_role': user_role,
    })


@login_required
def order_update(request, pk):
    user_role = get_user_role(request.user)
    order = get_object_or_404(Order, pk=pk)

    if user_role == 'guest':
        messages.error(request, 'У вас нет доступа.')
        return redirect('products:product_list')

    if user_role == 'client' and order.customer != request.user:
        messages.error(request, 'Вы можете редактировать только свои заказы.')
        return redirect('orders:order_list')

    if user_role == 'manager':
        if request.method == 'POST':
            form = OrderStatusForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                messages.success(request, 'Статус заказа обновлён.')
                return redirect('orders:order_list')
        else:
            form = OrderStatusForm(instance=order)
        return render(request, 'orders/order_status_form.html', {
            'form': form,
            'order': order,
            'user_role': user_role,
        })

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Заказ успешно обновлён.')
            return redirect('orders:order_list')
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)

    return render(request, 'orders/order_form.html', {
        'form': form,
        'formset': formset,
        'order': order,
        'title': 'Редактировать заказ',
        'user_role': user_role,
    })


@login_required
def order_delete(request, pk):
    user_role = get_user_role(request.user)
    order = get_object_or_404(Order, pk=pk)

    if user_role == 'guest':
        messages.error(request, 'У вас нет доступа.')
        return redirect('products:product_list')

    if user_role == 'manager':
        messages.error(request, 'У менеджера нет прав на удаление заказов.')
        return redirect('orders:order_list')

    if user_role == 'client' and order.customer != request.user:
        messages.error(request, 'Вы можете удалять только свои заказы.')
        return redirect('orders:order_list')

    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Заказ успешно удалён.')
        return redirect('orders:order_list')

    return render(request, 'orders/order_confirm_delete.html', {
        'order': order,
        'user_role': user_role,
    })
