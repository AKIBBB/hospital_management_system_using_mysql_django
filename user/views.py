from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.db import connection

from django.contrib.auth.hashers import check_password
def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user_type = request.POST.get('user_type', '') 
        image = request.FILES.get('image')

        specialization = request.POST.get('specialization', '').strip()
        fee = request.POST.get('fee', '').strip()

        if not all([first_name, last_name, email, password, user_type]):
            messages.error(request, "Please fill all required fields.")
            return redirect('register')

        if user_type == 'doctor' and not all([specialization, fee]):
            messages.error(request, "Specialization and fee are required for doctors.")
            return redirect('register')

        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", [email])
            if cursor.fetchone():
                messages.error(request, "Email already registered.")
                return redirect('register')

        image_path = None
        if image:
            fs = FileSystemStorage(location='media/profile_images')
            filename = fs.save(image.name, image)
            image_path = 'profile_images/' + filename

        hashed_password = make_password(password)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, password, image, user_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [first_name, last_name, email, hashed_password, image_path, user_type])

            user_id = cursor.lastrowid  

            if user_type == 'doctor':
                cursor.execute("""
                    INSERT INTO doctor (user_id, specialization, fee)
                    VALUES (%s, %s, %s)
                """, [user_id, specialization, fee])

        print("Registration successful, redirecting to login...")

        messages.success(request, "Registration successful! Please login.")
        return redirect('login')

    return render(request, 'user/register.html')




def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, password, first_name, user_type 
                FROM users 
                WHERE email = %s
            """, [email])
            row = cursor.fetchone()

        if row:
            user_id, hashed_password, first_name, user_type = row
            if check_password(password, hashed_password):
                request.session['user_id'] = user_id
                request.session['first_name'] = first_name
                request.session['user_type'] = user_type

                if user_type == 'doctor':
                    return redirect('dashboard')
                elif user_type == 'patient':
                    return redirect('index')
                elif user_type == 'admin':
                    return redirect('admin')
                else:
                    messages.error(request, "Unknown user type.")
            else:
                messages.error(request, "Incorrect password.")
        else:
            messages.error(request, "Email not found.")
        return redirect('login')

    return render(request, 'user/login.html')



def logout_view(request):
    request.session.flush()
    return redirect('login')





def dashboard_view(request):
    if request.session.get('user_type') != 'doctor':
        return redirect('login')

    doctor_user_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.appointment_id,
                p.id AS patient_id,
                p.first_name,
                p.last_name,
                p.email,
                a.appointment_date,
                a.status
            FROM appointment a
            JOIN users p ON a.patient_id = p.id
            JOIN doctor d ON a.doctor_id = d.doctor_id
            WHERE d.user_id = %s
            ORDER BY a.appointment_date DESC
        """, [doctor_user_id])

        appointments = cursor.fetchall()

    appointments_list = []
    for a in appointments:
        appointments_list.append({
            'appointment_id': a[0],
            'patient_id': a[1],
            'first_name': a[2],
            'last_name': a[3],
            'email': a[4],
            'appointment_date': a[5],
            'status': a[6],
        })

    return render(request, 'user/dashboard.html', {'appointments': appointments_list})




def index_view(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT category, service_name, description, image FROM service")
        services = cursor.fetchall()

    service_list = [
        {
            'category': row[0],
            'service_name': row[1],
            'description': row[2],
            'image': row[3],
        }
        for row in services
    ]

    return render(request, 'user/index.html', {'services': service_list})




from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

def admin_view(request):
    
    if request.session.get('user_type') != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    data = {}

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.doctor_id, u.first_name, u.last_name, d.specialization, u.email
            FROM doctor d
            JOIN users u ON d.user_id = u.id
        """)
        data['doctors'] = cursor.fetchall()

        cursor.execute("""
            SELECT id, first_name, last_name, email FROM users WHERE user_type='patient'
        """)
        data['patients'] = cursor.fetchall()

        cursor.execute("""
            SELECT a.appointment_id, u1.first_name AS patient_first, u1.last_name AS patient_last,
                   u2.first_name AS doctor_first, u2.last_name AS doctor_last, a.appointment_date, a.status
            FROM appointment a
            JOIN users u1 ON a.patient_id = u1.id
            JOIN doctor d ON a.doctor_id = d.doctor_id
            JOIN users u2 ON d.user_id = u2.id
        """)
        data['appointments'] = cursor.fetchall()

    return render(request, 'user/admin.html', data)


def add_doctor_view(request):
    if request.session.get('user_type') != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        specialization = request.POST.get('specialization')
        password = request.POST.get('password')  
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, user_type, password)
                VALUES (%s, %s, %s, 'doctor', %s)
            """, [first_name, last_name, email, password])
            user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO doctor (user_id, specialization) VALUES (%s, %s)
            """, [user_id, specialization])

        messages.success(request, "Doctor added successfully.")
        return redirect('admin')

    return render(request, 'user/add_doctor.html')


def remove_patient_view(request, patient_id):
    if request.session.get('user_type') != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id=%s AND user_type='patient'", [patient_id])
        messages.success(request, "Patient removed.")

    return redirect('admin')




def doctor_list_view(request):
    query = request.GET.get('query', '').strip()

    with connection.cursor() as cursor:
        if query:
            like_query = f"%{query}%"
            cursor.execute("""
                SELECT d.doctor_id, u.first_name, u.last_name, u.email, u.image, d.specialization, d.fee
                FROM doctor d
                JOIN users u ON d.user_id = u.id
                WHERE u.first_name LIKE %s OR u.last_name LIKE %s OR d.specialization LIKE %s
            """, [like_query, like_query, like_query])
        else:
            cursor.execute("""
                SELECT d.doctor_id, u.first_name, u.last_name, u.email, u.image, d.specialization, d.fee
                FROM doctor d
                JOIN users u ON d.user_id = u.id
            """)
        doctors = cursor.fetchall()

    doctor_list = []
    for d in doctors:
        doctor_list.append({
            'id': d[0],
            'first_name': d[1],
            'last_name': d[2],
            'email': d[3],
            'image': d[4],
            'specialization': d[5],
            'fee': d[6],
        })

    return render(request, 'user/index.html', {'doctors': doctor_list})



from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.decorators import login_required

def book_appointment_view(request):
    if not request.session.get('user_id'):
        return redirect('login')

   
    if request.session.get('user_type') not in ['patient', 'admin']:
        messages.error(request, "Only patients can book appointments.")
        return redirect('dashboard')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        appointment_date = request.POST.get('appointment_date') 

        if not doctor_id or not appointment_date:
            messages.error(request, "Please select a doctor and appointment date.")
            return redirect('book_appointment')

        patient_id = request.session.get('user_id')

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO appointment (patient_id, doctor_id, appointment_date)
                VALUES (%s, %s, %s)
            """, [patient_id, doctor_id, appointment_date])

        messages.success(request, "Appointment booked successfully!")
        return redirect('profile')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.doctor_id, u.first_name, u.last_name, d.specialization
            FROM doctor d
            JOIN users u ON d.user_id = u.id
        """)
        doctors = cursor.fetchall()

    doctors_list = [{
        'doctor_id': d[0],
        'first_name': d[1],
        'last_name': d[2],
        'specialization': d[3],
    } for d in doctors]

    return render(request, 'user/book_appointment.html', {'doctors': doctors_list})




def profile_view(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id:
        messages.error(request, "You must be logged in to view your profile.")
        return redirect('login')

    user_info = {}
    appointments = []
    prescriptions = []  

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, first_name, last_name, email, image, user_type 
            FROM users 
            WHERE id = %s
        """, [user_id])
        row = cursor.fetchone()
        if row:
            user_info = {
                'id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'email': row[3],
                'image': row[4],
                'user_type': row[5],
            }

    if user_type == 'patient':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.appointment_id, 
                    a.appointment_date, 
                    u.first_name, 
                    u.last_name
                FROM appointment a
                JOIN doctor d ON a.doctor_id = d.doctor_id
                JOIN users u ON d.user_id = u.id
                WHERE a.patient_id = %s
                ORDER BY a.appointment_date DESC
            """, [user_id])
            appointments = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    p.description, 
                    p.created_at, 
                    u.first_name, 
                    u.last_name
                FROM prescription p
                JOIN users u ON p.doctor_id = (
                    SELECT doctor_id FROM doctor WHERE doctor_id = p.doctor_id
                )
                JOIN doctor d ON d.doctor_id = p.doctor_id
                JOIN users doc_user ON d.user_id = doc_user.id
                WHERE p.patient_id = %s
                ORDER BY p.created_at DESC
            """, [user_id])
            prescriptions = cursor.fetchall()

    elif user_type == 'doctor':
        with connection.cursor() as cursor:
            cursor.execute("SELECT doctor_id FROM doctor WHERE user_id = %s", [user_id])
            doc_row = cursor.fetchone()

            if doc_row:
                doctor_id = doc_row[0]
                cursor.execute("""
                    SELECT 
                        a.appointment_id, 
                        a.appointment_date, 
                        u.first_name, 
                        u.last_name
                    FROM appointment a
                    JOIN users u ON a.patient_id = u.id
                    WHERE a.doctor_id = %s
                    ORDER BY a.appointment_date DESC
                """, [doctor_id])
                appointments = cursor.fetchall()

    return render(request, 'user/profile.html', {
        'user_info': user_info,
        'appointments': appointments,
        'prescriptions': prescriptions  
    })


from django.http import HttpResponseRedirect
from django.urls import reverse

def cancel_appointment_view(request, appointment_id):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    # Allow doctor OR admin
    if not user_id or user_type not in ['doctor', 'admin']:
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    with connection.cursor() as cursor:
        if user_type == 'doctor':
            # Doctors can only cancel their own appointments
            cursor.execute("""
                DELETE FROM appointment
                WHERE appointment_id = %s
                AND doctor_id = (SELECT doctor_id FROM doctor WHERE user_id = %s)
            """, [appointment_id, user_id])
        else:
            # Admins can cancel any appointment
            cursor.execute("DELETE FROM appointment WHERE appointment_id = %s", [appointment_id])

    messages.success(request, "Appointment cancelled successfully.")
    return redirect('admin' if user_type == 'admin' else 'dashboard')


from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

def update_appointment_view(request, appointment_id):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')

    if user_type not in ['doctor', 'admin']:
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        with connection.cursor() as cursor:
            if user_type == 'doctor':
                cursor.execute("""
                    UPDATE appointment
                    SET status = %s
                    WHERE appointment_id = %s
                    AND doctor_id = (SELECT doctor_id FROM doctor WHERE user_id = %s)
                """, [new_status, appointment_id, user_id])
            else:
                cursor.execute("""
                    UPDATE appointment
                    SET status = %s
                    WHERE appointment_id = %s
                """, [new_status, appointment_id])
        messages.success(request, "Appointment status updated.")
        return redirect('admin' if user_type == 'admin' else 'profile')

    # GET: show form
    with connection.cursor() as cursor:
        cursor.execute("SELECT status FROM appointment WHERE appointment_id = %s", [appointment_id])
        row = cursor.fetchone()
    current_status = row[0] if row else ''

    return render(request, 'user/update_appointment.html', {
        'appointment_id': appointment_id,
        'current_status': current_status
    })




# @csrf_exempt
# def update_appointment_view(request, appointment_id):
#     user_id = request.session.get('user_id')
#     user_type = request.session.get('user_type')

#     if not user_id or user_type != 'doctor':
#         messages.error(request, "Unauthorized access.")
#         return redirect('login')

#     if request.method == 'POST':
#         new_date = request.POST.get('new_date')
#         if not new_date:
#             messages.error(request, "New date is required.")
#             return redirect('profile')

#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 UPDATE appointment
#                 SET appointment_date = %s
#                 WHERE appointment_id = %s AND doctor_id = (
#                     SELECT doctor_id FROM doctor WHERE user_id = %s
#                 )
#             """, [new_date, appointment_id, user_id])

#         messages.success(request, "Appointment updated successfully.")
#     return redirect('profile')
from django.views.decorators.csrf import csrf_exempt






def prescribe_view(request, appointment_id):
    if request.session.get('user_type') != 'doctor':
        messages.error(request, "Only doctors can prescribe.")
        return redirect('login')

    if request.method == 'POST':
        description = request.POST.get('description', '').strip()

        if not description:
            messages.error(request, "Prescription text cannot be empty.")
            return redirect('prescribe', appointment_id=appointment_id)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT doctor_id, patient_id, status
                FROM appointment
                WHERE appointment_id = %s
            """, [appointment_id])
            result = cursor.fetchone()

            if not result:
                messages.error(request, "Appointment not found.")
                return redirect('dashboard')

            doctor_id, patient_id, status = result

            if status == 'Completed':
                messages.warning(request, "Prescription already given. Appointment is marked as completed.")
                return redirect('profile')

            cursor.execute("""
                INSERT INTO prescription (appointment_id, doctor_id, patient_id, description)
                VALUES (%s, %s, %s, %s)
            """, [appointment_id, doctor_id, patient_id, description])

            cursor.execute("""
                UPDATE appointment SET status = 'Completed' WHERE appointment_id = %s
            """, [appointment_id])

        messages.success(request, "Prescription saved and appointment marked as completed.")
        return redirect('profile')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT status FROM appointment WHERE appointment_id = %s
        """, [appointment_id])
        row = cursor.fetchone()

    if row and row[0] == 'Completed':
        messages.info(request, "Appointment already completed. Prescription cannot be modified.")
        return redirect('profile')

    return render(request, 'user/prescribe.html', {'appointment_id': appointment_id})




def prescribe_patient_view(request, appointment_id):
    if request.method == 'POST' and request.session.get('user_type') == 'doctor':
        description = request.POST.get('description')
        if description:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO prescription (appointment_id, description, created_at)
                    VALUES (%s, %s, NOW())
                """, [appointment_id, description])
            messages.success(request, "Prescription saved successfully.")
        else:
            messages.error(request, "Description cannot be empty.")
    return redirect('profile')





def services_view(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT category, service_name, description, image FROM service")
        services = cursor.fetchall()

    service_list = [
        {
            'category': s[0],
            'service_name': s[1],
            'description': s[2],
            'image': s[3]
        }
        for s in services
    ]

    return render(request, 'index.html', {'services': service_list})


from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO contact_messages (name, email, message)
                VALUES (%s, %s, %s)
            """, [name, email, message])

        messages.success(request, "Thank you for contacting us!")
        return redirect('index')  

    return redirect('index')


def add_patient_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if first_name and last_name and email and password:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, email, password, user_type)
                    VALUES (%s, %s, %s, %s, 'patient')
                """, [first_name, last_name, email, password])
                messages.success(request, "Patient added successfully!")
                return redirect('admin')
        else:
            messages.error(request, "All fields are required.")

    return render(request, 'user/add_patient.html')

def remove_doctor_view(request, doctor_id):
    if request.session.get('user_type') != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("SELECT user_id FROM doctor WHERE doctor_id=%s", [doctor_id])
        row = cursor.fetchone()
        if row:
            user_id = row[0]
            cursor.execute("DELETE FROM doctor WHERE doctor_id=%s", [doctor_id])
            cursor.execute("DELETE FROM users WHERE id=%s", [user_id])
            messages.success(request, "Doctor removed.")
        else:
            messages.error(request, "Doctor not found.")

    return redirect('admin')
