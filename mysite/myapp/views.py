from django.shortcuts import render, get_object_or_404,reverse,redirect
from .models import Product,OrderDetails
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponseNotFound
import stripe,json
from .forms import ProductForm,UserRegistrationForm
from django.db.models import Sum


# Create your views here.

def index(request):
    products = Product.objects.all()
    #if(products!=' '):
    return render(request,'index.html',{'products':products})
    # else:
    # return render(request,'index.html')

def detail(request,id):
   product = Product.objects.get(id=id)
   return render(request,'detail.html',{'product':product,'stripe_publishable_key':'stripe_publishable_key'
})

@csrf_exempt

def Create_checkout_session(request,id):
    request_data = json.loads(request.body)
    product = Product.objects.get(id=id)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session = stripe.checkout.Session.create(
        customer_email = request_data['email'],
        payment_method_types = ['card'],
        line_items=[
            {
                'price_data':{
                    'currency':'usd',
                    'product_data':{
                        'name':product.name,
                    },
                    'unit_amount':int(product.price * 100)
                },
                'quantity':1,
            }
        ],
        mode='payment',
        success_url = request.build_absolute_uri(reverse('success'))+
        "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url = request.__build_absolute_uri(reverse('failed')),
    )

    order = OrderDetails()
    order.customer_email = request_data['email']
    order.product = product
    order.stripe_payment_intent = checkout_session['payment_intent']
    order.amount = int(product.price)
    order.save()

    return JsonResponse({'sessionId':checkout_session.id})

def payment_success_view(request):
    session_id = request.GET.get('session_id')
    if session_id is None:
        return HttpResponseNotFound()
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(session_id)
    order = get_object_or_404(OrderDetails,stripe_payment_intent= session.payment_intent)
    order.has_paid= True
    # Updating sales start for a product
    product= Product.objects.get(id=order.product.id)
    product.total_sales_amount= product.total_sales_amount+(product.price)
    product.total_sales_amount= product.total_sales_amount+1
    product.save()
    # Updating sales start for a product
    order.save()

    return render(request,'payment_success.html',{'order':order})

def payment_failed_view(request):
    return render(request, 'failed.html')

def create_product(request):
    if request.method=='POST':
        product_form = ProductForm(request.POST,request.FILES)
        if product_form.is_valid():
            new_product = product_form.save(commit=False)
            new_product.seller= request.user
            new_product.save()
            return redirect('index')

    product_form = ProductForm()
    return render(request, 'create_product.html',{'product_form': product_form})

def product_edit(request,id):
    product = Product.objects.get(id=id)
    # if product.seller != request.user:
    #     return redirect('invalid')
    product_form = ProductForm(request.POST or None,request.FILES or None,instance=product)
    if request.method=='POST':
        if product_form.is_valid():
            product_form.save()
            return redirect('index')

    return render(request,'product_edit.html',{'product_form': product_form,'product':product})


def product_delete(request,id):
    product= Product.objects.get(id=id)
    # if product.seller != request.user:
    #     return redirect('invalid')
    if request.method=='POST':
        product.delete()
        return redirect('index')
    return render(request,'delete.html',{'product': product})

def dashboard(request):
    products=Product.objects.filter(seller=request.user)
    return render(request, 'dashboard.html',{'products':products})

def register(request):
    if request.method=='POST':
        user_form=UserRegistrationForm(request.POST)
        new_user = user_form.save(commit=False)
        new_user.set_password(user_form.cleaned_data['password'])
        new_user.save()
        return redirect('index')
    user_form=UserRegistrationForm()
    return render(request,'register.html',{'user_form':user_form})

def invalid(request):
    return render(request,'invalid.html')

def my_purchases(request):
    orders = OrderDetails.objects.all()
    # orders = OrderDetails.objects.filter(customer_email=request.user.email)
    return render(request,'purchases.html',{'orders':orders})

def sales(request):
    orders = OrderDetails.objects.filter(product__seller=request.user)
    total_sales=orders.aaggregate(Sum('amount'))
    # print(total_sales)
    return render(request,'sales.html',{'total_sales':total_sales})