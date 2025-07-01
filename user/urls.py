from django.urls import path
from .views import register_view, login_view, logout_view, dashboard_view,doctor_list_view,book_appointment_view,profile_view,cancel_appointment_view,index_view,admin_view,update_appointment_view,prescribe_view,prescribe_patient_view,services_view,contact_view,remove_doctor_view,add_doctor_view,add_patient_view,remove_patient_view


urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('index/', index_view, name='index'),              # for patients
    path('myadmin/', admin_view, name='admin'), 
    path('doctors/', doctor_list_view, name='doctor_list'),
    path('book-appointment/', book_appointment_view, name='book_appointment'),
    path('profile/', profile_view, name='profile'),
    path('cancel-appointment/<int:appointment_id>/', cancel_appointment_view, name='cancel_appointment'),
    path('update-appointment/<int:appointment_id>/', update_appointment_view, name='update_appointment'),
    path('prescribe/<int:appointment_id>/', prescribe_view, name='prescribe'),
    path('prescribe/<int:appointment_id>/', prescribe_patient_view, name='prescribe_patient'),
    path('services/', services_view, name='services'),
    path('contact/', contact_view, name='contact'),
    
    
    path('remove-doctor/<int:doctor_id>/', remove_doctor_view, name='remove_doctor'),
    path('add-doctor/', add_doctor_view, name='add_doctor'),

    path('add-patient/', add_patient_view, name='add_patient'),
    path('remove-patient/<int:patient_id>/', remove_patient_view, name='remove_patient'),

    


]
