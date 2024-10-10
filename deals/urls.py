from django.urls import path
from .views import deals_view, index, signup, login, update_deal_view, logout_view, comment_view, deal_detail, jazzcash_payment, jazzcash_response, checkout_view, cashjazz, success_get
from django.contrib.auth.views import LogoutView
urlpatterns = [
    path('', index, name='index'),
    path('signup/', signup, name='signup'),
    path('login/', login, name='login'),
    path('deals_view/', deals_view, name='deals_view'),
    #path('verify_otp/', verify_otp, name='verify_otp'),
    path('logout/', logout_view, name='logout_view'),
    path('update_deal/<str:deal_id>/', update_deal_view, name='update_deal_view'),
    path('comment/<str:deal_id>/', comment_view, name='comment_view'),
    path('deal/<str:deal_id>/', deal_detail, name='deal_detail'),
    path('jazzcash-payment/', jazzcash_payment, name='jazzcash_payment'),
    path('jazzcash-response/', jazzcash_response, name='jazzcash_response'),
    path('checkout/', checkout_view, name='checkout'),
    path('cashjazz/', cashjazz, name='cashjazz'),
    path('success', success_get, name='success_get'),
    #path('logout/', LogoutView.as_view(next_page='/login/'), name='logout')
]
