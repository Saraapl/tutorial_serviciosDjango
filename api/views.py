from rest_framework import generics, permissions
from todo.models import ToDo
from .serializers import ToDoSerializer, TodoToggleCompleteSerializer
from django.db import IntegrityError
from django.contrib.auth.models import User
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from rest_framework.exceptions import ParseError


class ToDoListCreate(generics.ListCreateAPIView):
    serializer_class = ToDoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ToDo.objects.filter(user=user).order_by('-created')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TodoRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ToDoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # user can only update, delete own posts
        return ToDo.objects.filter(user=user)


class TodoToggleComplete(generics.UpdateAPIView):
    serializer_class = TodoToggleCompleteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ToDo.objects.filter(user=user)

    def perform_update(self, serializer):
        serializer.instance.completed = not serializer.instance.completed
        serializer.save()


@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            # Check if request has JSON content
            if not request.body:
                return JsonResponse({'error': 'No data provided'}, status=400)

            data = JSONParser().parse(request)  # data is a dictionary
            user = User.objects.create_user(
                username=data['username'],
                password=data['password']
            )
            user.save()
            token = Token.objects.create(user=user)
            return JsonResponse({'token': str(token)}, status=201)
        except IntegrityError:
            return JsonResponse(
                {'error': 'username taken. choose another username'},
                status=400
            )
        except KeyError:
            return JsonResponse(
                {'error': 'username and password are required'},
                status=400
            )
        except ParseError:
            return JsonResponse(
                {'error': 'Invalid JSON format'},
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)},
                status=400
            )
    else:
        # Handle GET requests or other methods
        return JsonResponse(
            {'error': 'Method not allowed. Use POST with JSON data'},
            status=405
        )


@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            # Check if request has JSON content
            if not request.body:
                return JsonResponse({'error': 'No data provided'}, status=400)

            data = JSONParser().parse(request)
            user = authenticate(
                request,
                username=data['username'],
                password=data['password']
            )
            if user is None:
                return JsonResponse(
                    {'error': 'unable to login. check username and password'},
                    status=400
                )
            else:  # return user token
                try:
                    token = Token.objects.get(user=user)
                except Token.DoesNotExist:  # if token not in db, create a new one
                    token = Token.objects.create(user=user)
                return JsonResponse({'token': str(token)}, status=200)
        except KeyError:
            return JsonResponse(
                {'error': 'username and password are required'},
                status=400
            )
        except ParseError:
            return JsonResponse(
                {'error': 'Invalid JSON format'},
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)},
                status=400
            )
    else:
        # Handle GET requests or other methods
        return JsonResponse(
            {'error': 'Method not allowed. Use POST with JSON data'},
            status=405
        )