import os
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse

# Load users from a JSON file relative to the Django project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE_PATH = os.path.join(BASE_DIR, 'my_gym_app', 'users.json')

def load_users():
    if os.path.exists(USERS_FILE_PATH):
        with open(USERS_FILE_PATH, 'r') as file:
            return json.load(file)
    return []

def save_users(users):
    with open(USERS_FILE_PATH, 'w') as file:
        json.dump(users, file, indent=4)

USERS_DATA = load_users()

# Login page view
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = next((user for user in USERS_DATA if user['username'] == username and user['password'] == password), None)

        if user:
            request.session['user'] = user
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')

# Dashboard page view
def dashboard(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')

    if request.method == 'POST' and user['type'] == 'manager':
        action = request.POST.get('action')
        if action == 'add':
            new_user = {
                'username': request.POST['username'],
                'password': request.POST['password'],
                'type': request.POST['type']
            }
            USERS_DATA.append(new_user)
            save_users(USERS_DATA)

        elif action == 'edit':
            username = request.POST['username']
            for u in USERS_DATA:
                if u['username'] == username:
                    u['password'] = request.POST['password']
                    u['type'] = request.POST['type']
                    break
            save_users(USERS_DATA)

        elif action == 'remove':
            username = request.POST['username']
            USERS_DATA[:] = [u for u in USERS_DATA if u['username'] != username]
            save_users(USERS_DATA)

    return render(request, 'dashboard.html', {'user': user, 'users': USERS_DATA})

# Logout view
def logout_view(request):
    if 'user' in request.session:
        del request.session['user']
    return redirect('login')
