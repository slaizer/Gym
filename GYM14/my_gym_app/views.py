import os
import json
from django.shortcuts import render, redirect
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# File paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE_PATH = os.path.join(BASE_DIR, 'my_gym_app', 'users.json')
COURSES_FILE_PATH = os.path.join(BASE_DIR, 'my_gym_app', 'workouts.json')
# New file paths for videos
WORKOUT_VIDEOS_FILE_PATH = os.path.join(BASE_DIR, 'my_gym_app', 'workout_videos.json')
COOKING_VIDEOS_FILE_PATH = os.path.join(BASE_DIR, 'my_gym_app', 'cooking_videos.json')
def load_data(file_path):
    """Load data from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_data(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Load initial data
USERS_DATA = load_data(USERS_FILE_PATH)
COURSES_DATA = load_data(COURSES_FILE_PATH)

def is_username_taken(username):
    """Check if a username already exists in the users data."""
    return any(u['username'].lower() == username.lower() for u in USERS_DATA)

# Login page
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = next((u for u in USERS_DATA if u['username'] == username and u['password'] == password), None)

        if user:
            request.session['user'] = user
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')

# Dashboard page
def dashboard(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')

    # Load workout and food data
    workouts = load_data(COURSES_FILE_PATH)  # Load workout data
    food_data = load_data('food.json')  # Load food data

    if user['type'] == 'manager':
        # For manager, simply render the dashboard with any needed data.
        # You can extend this section later if you want to display more info for managers.
        return render(request, 'dashboard.html', {
            'user': user,
            'workouts': workouts,
            'food_data': food_data
        })

    elif user['type'] == 'captin':
        # Captains manage courses and food for their assigned users
        managed_users = [u for u in USERS_DATA if u.get('assigned_to') == user['username']]
        return render(request, 'dashboard.html', {
            'user': user,
            'managed_users': managed_users,
            'workouts': workouts,
            'food_data': food_data
        })

    elif user['type'] == 'user':
        # Users view their own courses and food
        user_workouts = next((w for w in workouts if w['user'] == user['username']), None)
        if not user_workouts:
            user_workouts = {'user': user['username'], 'workouts': []}
            workouts.append(user_workouts)
            save_data(COURSES_FILE_PATH, workouts)

        user_food = next((f for f in food_data if f['user'] == user['username']), None)
        if not user_food:
            user_food = {'user': user['username'], 'meals': []}
            food_data.append(user_food)
            save_data('food.json', food_data)

        # Load videos from the assigned captain, if any
        assigned_captain = user.get('assigned_to')
        if assigned_captain:
            workout_videos = [v for v in load_data(WORKOUT_VIDEOS_FILE_PATH) if v.get('captin') == assigned_captain]
            cooking_videos = [v for v in load_data(COOKING_VIDEOS_FILE_PATH) if v.get('captin') == assigned_captain]
        else:
            workout_videos = []
            cooking_videos = []

        return render(request, 'dashboard.html', {
            'user': user,
            'courses': user_workouts['workouts'],
            'meals': user_food['meals'],
            'workout_videos': workout_videos,
            'cooking_videos': cooking_videos
        })

    # Optional: Add a default return in case the user type is unknown.
    return redirect('login')


def manage_users(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')

    # Only manager or captain can access this view
    if user['type'] not in ['manager', 'captin']:
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        # 1. Add a new user
        if action == 'add':
            new_username = request.POST['username']
            new_password = request.POST['password']
            new_type = request.POST['type']

            # Check if the username already exists
            if is_username_taken(new_username):
                return render(request, 'manage_users.html', {
                    'user': user,
                    'users': USERS_DATA,
                    'error': 'Username already exists.'
                })
            else:
                # Managers can add any type; Captains can only add 'user'
                if user['type'] == 'manager' or (user['type'] == 'captin' and new_type == 'user'):
                    new_user = {
                        'username': new_username,
                        'password': new_password,
                        'type': new_type
                    }
                    USERS_DATA.append(new_user)
                    save_data(USERS_FILE_PATH, USERS_DATA)

        # 2. Edit an existing user
        elif action == 'edit':
            edit_username = request.POST.get('username')
            new_password = request.POST.get('password', '').strip()
            new_type = request.POST.get('type', '').strip()

            for existing_user in USERS_DATA:
                if existing_user['username'] == edit_username:
                    # Update password if provided
                    if new_password:
                        existing_user['password'] = new_password

                    # Managers can edit any type; Captains can only set type to 'user'
                    if user['type'] == 'manager':
                        existing_user['type'] = new_type
                    elif user['type'] == 'captin' and new_type == 'user':
                        existing_user['type'] = new_type

                    save_data(USERS_FILE_PATH, USERS_DATA)
                    break

        # 3. Remove an existing user
        elif action == 'remove':
            remove_username = request.POST.get('username')

            for i, existing_user in enumerate(USERS_DATA):
                # Managers can remove any user; Captains can only remove 'user' accounts
                if (user['type'] == 'manager' or
                    (user['type'] == 'captin' and existing_user['type'] == 'user')):
                    if existing_user['username'] == remove_username:
                        USERS_DATA.pop(i)
                        save_data(USERS_FILE_PATH, USERS_DATA)
                        break

    return render(request, 'manage_users.html', {
        'user': user,
        'users': USERS_DATA
    })

def manage_courses(request, username):
    user = request.session.get('user')
    if not user or user['type'] != 'captin':
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            new_course = {
                'course_id': len(COURSES_DATA) + 1,
                'user': username,
                'name': request.POST['name'],
                'description': request.POST['description'],
            }
            COURSES_DATA.append(new_course)
            save_data(COURSES_FILE_PATH, COURSES_DATA)

        elif action == 'edit':
            course_id = int(request.POST['course_id'])
            for c in COURSES_DATA:
                if c['course_id'] == course_id:
                    c['name'] = request.POST['name']
                    c['description'] = request.POST['description']
                    break
            save_data(COURSES_FILE_PATH, COURSES_DATA)

    user_courses = [c for c in COURSES_DATA if c['user'] == username]
    return render(request, 'manage_courses.html', {'user': user, 'username': username, 'courses': user_courses})

# Logout view
def logout_view(request):
    if 'user' in request.session:
        del request.session['user']
    return redirect('login')

# Assign users to captains (managers only)
def assign_users(request):
    user = request.session.get('user')
    if not user or user['type'] != 'manager':
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        assigned_to = request.POST['captin']

        for u in USERS_DATA:
            if u['username'] == username:
                u['assigned_to'] = assigned_to
                break

        save_data(USERS_FILE_PATH, USERS_DATA)

    # Get all users (excluding managers) and captains
    users = [u for u in USERS_DATA if u['type'] == 'user']
    captins = [u for u in USERS_DATA if u['type'] == 'captin']

    return render(request, 'assign_users.html', {'user': user, 'users': users, 'captins': captins})

# Manage workouts for a specific user (captain only)
def manage_workouts(request, username):
    user = request.session.get('user')
    if not user or user['type'] != 'captin':
        return redirect('dashboard')

    # Load data from JSON
    workouts = load_data(COURSES_FILE_PATH)
    user_workouts = next((w for w in workouts if w['user'] == username), None)

    if not user_workouts:
        user_workouts = {'user': username, 'workouts': []}
        workouts.append(user_workouts)
        save_data(COURSES_FILE_PATH, workouts)

    # Preprocess repeats and weights
    for day in user_workouts['workouts']:
        for exercise in day['exercises']:
            exercise['repeats'] = (exercise.get('repeats', []) + [""] * 5)[:5]
            exercise['weights'] = (exercise.get('weights', []) + [""] * 5)[:5]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_day':
            # Add a new workout day
            new_day = {
                'day': f"Day{len(user_workouts['workouts']) + 1}",
                'exercises': []
            }
            user_workouts['workouts'].append(new_day)
            save_data(COURSES_FILE_PATH, workouts)

        elif action == 'add_exercise':
            # Add a new exercise to a specific day
            day = request.POST.get('day')
            exercise = {
                'name': request.POST['exercise'],
                'repeats': [request.POST.get(f'repeats_new_{i}', '') for i in range(1, 6)],
                'weights': [request.POST.get(f'weights_new_{i}', '') for i in range(1, 6)],
                'priority': int(request.POST.get('priority', 0))
            }
            exercise['repeats'] = [r for r in exercise['repeats'] if r]
            exercise['weights'] = [w for w in exercise['weights'] if w]
            for w in user_workouts['workouts']:
                if w['day'] == day:
                    w['exercises'].append(exercise)
                    # Sort exercises by priority
                    w['exercises'].sort(key=lambda x: x['priority'])
                    break
            save_data(COURSES_FILE_PATH, workouts)

        elif action == 'remove_exercise':
            # Remove an exercise from a specific day
            day = request.POST.get('day')
            exercise_name = request.POST.get('exercise_name')
            for w in user_workouts['workouts']:
                if w['day'] == day:
                    w['exercises'] = [e for e in w['exercises'] if e['name'] != exercise_name]
                    break
            save_data(COURSES_FILE_PATH, workouts)

        elif action == 'remove_day':
            # Remove a workout day
            day = request.POST.get('day')
            user_workouts['workouts'] = [w for w in user_workouts['workouts'] if w['day'] != day]
            save_data(COURSES_FILE_PATH, workouts)

    # Render the page
    return render(request, 'manage_workouts.html', {
        'user': user,
        'username': username,
        'workouts': user_workouts['workouts'],
        'range': range(1, 6)
    })

def manage_food(request, username):
    user = request.session.get('user')
    if not user or user['type'] != 'captin':
        return redirect('dashboard')

    # Load data from JSON (ensure the correct file path for food data)
    food_data = load_data('food.json')
    user_food = next((f for f in food_data if f['user'] == username), None)

    if not user_food:
        # Initialize food data for the user if it doesn't exist
        user_food = {'user': username, 'meals': []}
        food_data.append(user_food)
        save_data('food.json', food_data)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_day':
            # Add a new meal day
            new_day = {'day': f"Day{len(user_food['meals']) + 1}", 'items': []}
            user_food['meals'].append(new_day)

        elif action == 'add_item':
            # Add a new food item to a specific day
            day = request.POST.get('day')
            item = {
                'name': request.POST.get('item'),
                'calories': request.POST.get('calories'),
                'priority': int(request.POST.get('priority', 0))
            }
            for meal in user_food['meals']:
                if meal['day'] == day:
                    meal['items'].append(item)
                    meal['items'].sort(key=lambda x: x['priority'])
                    break

        elif action == 'remove_item':
            # Remove a specific food item from a day
            day = request.POST.get('day')
            item_name = request.POST.get('item_name')
            for meal in user_food['meals']:
                if meal['day'] == day:
                    meal['items'] = [i for i in meal['items'] if i['name'] != item_name]
                    break

        elif action == 'remove_day':
            # Remove an entire day
            day = request.POST.get('day')
            user_food['meals'] = [m for m in user_food['meals'] if m['day'] != day]

        # Save updated data
        save_data('food.json', food_data)

    return render(request, 'manage_food.html', {
        'user': user,
        'username': username,
        'meals': user_food['meals']
    })

def captin_manage_users(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')

    # Ensure only a captain can access this page
    if user['type'] != 'captin':
        return redirect('dashboard')

    # Filter the USERS_DATA to show only the users assigned to this captain
    my_users = [u for u in USERS_DATA if u.get('assigned_to') == user['username']]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            new_username = request.POST.get('username')
            new_password = request.POST.get('password', '')
            new_type = 'user'  # Captains can only add 'user' type

            # Check if the username already exists
            if is_username_taken(new_username):
                return render(request, 'captin_manage_users.html', {
                    'user': user,
                    'my_users': my_users,
                    'error': 'Username already exists.'
                })
            else:
                # Build the new user object
                new_user = {
                    'username': new_username,
                    'password': new_password,
                    'type': new_type,
                    'assigned_to': user['username']  # auto-assign to this captain
                }
                USERS_DATA.append(new_user)
                save_data(USERS_FILE_PATH, USERS_DATA)

        elif action == 'edit':
            edit_username = request.POST.get('username')
            new_password = request.POST.get('password', '').strip()
            # For captain, type changes are restricted to 'user' only
            for existing_user in USERS_DATA:
                if existing_user['username'] == edit_username:
                    # Update password if provided
                    if new_password:
                        existing_user['password'] = new_password
                    # We do not change user type to anything but 'user' if requested
                    existing_user['type'] = 'user'
                    save_data(USERS_FILE_PATH, USERS_DATA)
                    break

        elif action == 'remove':
            remove_username = request.POST.get('username')
            for i, existing_user in enumerate(USERS_DATA):
                # Captains can only remove 'user' accounts
                if (
                        existing_user['username'] == remove_username
                        and existing_user['type'] == 'user'
                        and existing_user.get('assigned_to') == user['username']
                ):
                    USERS_DATA.pop(i)
                    save_data(USERS_FILE_PATH, USERS_DATA)
                    break

    # Refresh my_users after any changes
    my_users = [u for u in USERS_DATA if u.get('assigned_to') == user['username']]

    return render(request, 'captin_manage_users.html', {
        'user': user,
        'my_users': my_users
    })


def manage_workout_videos(request):
    """
    Allows a captain to add, edit, and remove YouTube workout videos.
    """
    user = request.session.get('user')
    if not user or user['type'] != 'captin':
        return redirect('dashboard')

    # Load all workout videos
    videos = load_data(WORKOUT_VIDEOS_FILE_PATH)
    # Filter videos that belong to the current captain
    my_videos = [v for v in videos if v.get('captin') == user['username']]

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            new_video = {
                'video_id': len(videos) + 1,  # simple incremental id
                'captin': user['username'],
                'youtube_url': request.POST.get('youtube_url'),
                'title': request.POST.get('title'),
                'description': request.POST.get('description'),
                'priority': int(request.POST.get('priority', 0))
            }
            videos.append(new_video)
            save_data(WORKOUT_VIDEOS_FILE_PATH, videos)
        elif action == 'edit':
            video_id = int(request.POST.get('video_id'))
            for v in videos:
                if v['video_id'] == video_id and v.get('captin') == user['username']:
                    v['youtube_url'] = request.POST.get('youtube_url')
                    v['title'] = request.POST.get('title')
                    v['description'] = request.POST.get('description')
                    v['priority'] = int(request.POST.get('priority', 0))
                    break
            save_data(WORKOUT_VIDEOS_FILE_PATH, videos)
        elif action == 'remove':
            video_id = int(request.POST.get('video_id'))
            # Remove the video that matches the video_id and belongs to the current captain
            videos = [v for v in videos if not (v['video_id'] == video_id and v.get('captin') == user['username'])]
            save_data(WORKOUT_VIDEOS_FILE_PATH, videos)

        # Refresh the list after changes
        my_videos = [v for v in videos if v.get('captin') == user['username']]

    return render(request, 'manage_workout_videos.html', {'user': user, 'videos': my_videos})


def manage_cooking_videos(request):
    """
    Allows a captain to add, edit, and remove YouTube cooking videos.
    """
    user = request.session.get('user')
    if not user or user['type'] != 'captin':
        return redirect('dashboard')

    # Load all cooking videos
    videos = load_data(COOKING_VIDEOS_FILE_PATH)
    # Filter videos that belong to the current captain
    my_videos = [v for v in videos if v.get('captin') == user['username']]

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            new_video = {
                'video_id': len(videos) + 1,
                'captin': user['username'],
                'youtube_url': request.POST.get('youtube_url'),
                'title': request.POST.get('title'),
                'description': request.POST.get('description'),
                'priority': int(request.POST.get('priority', 0))
            }
            videos.append(new_video)
            save_data(COOKING_VIDEOS_FILE_PATH, videos)
        elif action == 'edit':
            video_id = int(request.POST.get('video_id'))
            for v in videos:
                if v['video_id'] == video_id and v.get('captin') == user['username']:
                    v['youtube_url'] = request.POST.get('youtube_url')
                    v['title'] = request.POST.get('title')
                    v['description'] = request.POST.get('description')
                    v['priority'] = int(request.POST.get('priority', 0))
                    break
            save_data(COOKING_VIDEOS_FILE_PATH, videos)
        elif action == 'remove':
            video_id = int(request.POST.get('video_id'))
            videos = [v for v in videos if not (v['video_id'] == video_id and v.get('captin') == user['username'])]
            save_data(COOKING_VIDEOS_FILE_PATH, videos)

        my_videos = [v for v in videos if v.get('captin') == user['username']]

    return render(request, 'manage_cooking_videos.html', {'user': user, 'videos': my_videos})


def upload_video_link(request):
    """
    Allows a captain to upload a new video link (either a workout or cooking video).
    The video link will be saved to the appropriate JSON file and then be displayed
    on the dashboards of users assigned to that captain.
    """
    user = request.session.get('user')
    if not user or user['type'] != 'captin':
        return redirect('dashboard')

    # Initialize error and success messages
    error = None
    success_msg = None

    # Pre-load the uploaded videos for the current captain
    uploaded_workout_videos = [v for v in load_data(WORKOUT_VIDEOS_FILE_PATH) if v.get('captin') == user['username']]
    uploaded_cooking_videos = [v for v in load_data(COOKING_VIDEOS_FILE_PATH) if v.get('captin') == user['username']]

    if request.method == 'POST':
        # Get form data
        video_type = request.POST.get('video_type')  # Expected values: 'workout' or 'cooking'
        youtube_url = request.POST.get('youtube_url')
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 0)

        try:
            priority = int(priority)
        except ValueError:
            priority = 0

        # Determine the correct JSON file path based on video type
        if video_type == 'workout':
            file_path = WORKOUT_VIDEOS_FILE_PATH
        elif video_type == 'cooking':
            file_path = COOKING_VIDEOS_FILE_PATH
        else:
            error = "Invalid video type provided."
            context = {
                'user': user,
                'error': error,
                'uploaded_workout_videos': uploaded_workout_videos,
                'uploaded_cooking_videos': uploaded_cooking_videos,
            }
            return render(request, 'upload_video.html', context)

        # Load existing videos from the file
        videos = load_data(file_path)
        new_video = {
            'video_id': len(videos) + 1,  # Simple incremental ID
            'captin': user['username'],
            'youtube_url': youtube_url,
            'title': title,
            'description': description,
            'priority': priority
        }
        videos.append(new_video)
        save_data(file_path, videos)

        success_msg = "Video link uploaded successfully."

        # Update the uploaded videos lists after a new upload
        uploaded_workout_videos = [v for v in load_data(WORKOUT_VIDEOS_FILE_PATH) if v.get('captin') == user['username']]
        uploaded_cooking_videos = [v for v in load_data(COOKING_VIDEOS_FILE_PATH) if v.get('captin') == user['username']]

    context = {
        'user': user,
        'error': error,
        'success': success_msg,
        'uploaded_workout_videos': uploaded_workout_videos,
        'uploaded_cooking_videos': uploaded_cooking_videos,
    }
    return render(request, 'upload_video.html', context)


def remove_video(request, video_type, video_id):
    """
    Removes a video link uploaded by the current captain.
    Expects 'video_type' to be either 'workout' or 'cooking'.
    """
    user = request.session.get('user')
    if not user or user['type'] != 'captin':
        return redirect('dashboard')

    # Determine the file path based on video type
    if video_type == 'workout':
        file_path = WORKOUT_VIDEOS_FILE_PATH
    elif video_type == 'cooking':
        file_path = COOKING_VIDEOS_FILE_PATH
    else:
        # Invalid video type; simply redirect back
        return redirect('upload_video_link')

    # Load existing videos from the file
    videos = load_data(file_path)

    # Filter out the video to be removed (make sure it belongs to the current captain)
    new_videos = [v for v in videos if not (v.get('video_id') == video_id and v.get('captin') == user['username'])]

    # Save the updated videos list if a removal occurred
    if len(new_videos) != len(videos):
        save_data(file_path, new_videos)

    return redirect('upload_video_link')
def base_page(request):
    return render(request, 'base.html')


def update_weight(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            day = data.get('day')
            exercise_name = data.get('exercise_name')
            exercise_index = int(data.get('exercise_index'))
            weight_index = int(data.get('weight_index'))
            new_value = data.get('new_value')

            # Ensure user is logged in and is of type 'user'
            user = request.session.get('user')
            if not user or user['type'] != 'user':
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

            # Load the workouts from the JSON file.
            with open(COURSES_FILE_PATH, 'r') as f:
                workouts = json.load(f)

            # Find the current user's workout record.
            user_workouts = next((w for w in workouts if w['user'] == user['username']), None)
            if not user_workouts:
                return JsonResponse({'success': False, 'error': 'Workout record not found'}, status=404)

            # Locate the correct day record.
            for day_record in user_workouts.get('workouts', []):
                if day_record.get('day') == day:
                    # Find the exercise by its index.
                    try:
                        exercise = day_record['exercises'][exercise_index]
                    except IndexError:
                        return JsonResponse({'success': False, 'error': 'Exercise not found'}, status=404)

                    # Update the weight at the given index.
                    try:
                        exercise['weights'][weight_index] = new_value
                    except IndexError:
                        return JsonResponse({'success': False, 'error': 'Weight index out of range'}, status=404)

                    # Save the updated workouts back to the JSON file.
                    with open(COURSES_FILE_PATH, 'w') as f:
                        json.dump(workouts, f, indent=4)
                    return JsonResponse({'success': True})

            return JsonResponse({'success': False, 'error': 'Day not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)