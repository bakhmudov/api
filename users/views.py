from django.contrib.auth import authenticate
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework import status
from rest_framework.generics import DestroyAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, File, FileAccess
from .permissions import IsOwnerOrReadOnly
from .serializers import FileSerializer, FileAccessSerializer


class RegisterAPIView(APIView):
    def post(self, request):
        # Получаем данные из запроса
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        # Проверяем, что все необходимые данные присутствуют
        errors = {}
        if not email:
            errors['email'] = ['Field email can not be blank']
        if not password:
            errors['password'] = ['Field password can not be blank']
        if not first_name:
            errors['first_name'] = ['Field first_name can not be blank']
        if not last_name:
            errors['last_name'] = ['Field last_name can not be blank']

        # Если есть ошибки валидации, возвращаем ответ с соответствующими данными об ошибке
        if errors:
            return Response({'success': False, 'message': errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Создаем пользователя
        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Генерируем токен для нового пользователя
        refresh = RefreshToken.for_user(user)

        # Возвращаем успешный ответ с токеном
        return Response({'success': True, 'message': 'Success', 'token': str(refresh.access_token)},
                        status=status.HTTP_200_OK)


class AuthorizationAPIView(APIView):
    def post(self, request):
        # Получаем данные из запроса
        email = request.data.get('email')
        password = request.data.get('password')

        # Проверяем, что все необходимые данные присутствуют
        if not email or not password:
            return Response({'success': False, 'message': 'Email and password are required'},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Проводим аутентификацию пользователя
        user = authenticate(request, username=email, password=password)

        # Если пользователь не найден или пароль неверен, возвращаем ошибку аутентификации
        if not user:
            return Response({'success': False, 'message': 'Login failed'}, status=status.HTTP_401_UNAUTHORIZED)

        # Если аутентификация прошла успешно, генерируем токен для пользователя
        refresh = RefreshToken.for_user(user)

        # Возвращаем успешный ответ с токеном
        return Response({'success': True, 'message': 'Success', 'token': str(refresh.access_token)},
                        status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # Только аутентифицированные пользователи могут выходить

    def get(self, request):
        # Очистите токен пользователя или выполняйте другие действия, связанные с выходом
        # Например, вы можете удалять токен из базы данных или удалять его из куки, если используете JWT

        # Возвратите успешный ответ
        return Response({"success": True, "message": "Logout"})


ALLOWED_FILE_TYPES = ['doc', 'pdf', 'docx', 'zip', 'jpeg', 'jpg', 'png']
MAX_FILE_SIZE_MB = 2


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        files = request.FILES.getlist('files')

        responses = []
        for uploaded_file in files:
            # Проверяем размер файла
            if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                responses.append({
                    "success": False,
                    "message": "File size exceeds the limit of 2MB",
                    "name": uploaded_file.name
                })
                continue

            # Проверяем тип файла
            file_type = uploaded_file.name.split('.')[-1]
            if file_type.lower() not in ALLOWED_FILE_TYPES:
                responses.append({
                    "success": False,
                    "message": "File type not allowed",
                    "name": uploaded_file.name
                })
                continue

            data = {'file': uploaded_file, 'user': request.user.id}

            serializer = FileSerializer(data=data)
            if serializer.is_valid():
                # Если сериализатор валиден, сохраняем объект File
                file_obj = serializer.save()
                responses.append({
                    "success": True,
                    "message": "Success",
                    "name": uploaded_file.name,
                    "url": file_obj.file.url,
                    "file_id": file_obj.file_id
                })
            else:
                responses.append({
                    "success": False,
                    "message": serializer.errors,
                    "name": uploaded_file.name
                })

        if any(response['success'] is False for response in responses):
            return Response(responses, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            return Response(responses, status=status.HTTP_200_OK)


class FileEditView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, file_id):
        # Получаем файл по его идентификатору, если он существует
        file_instance = get_object_or_404(File, id=file_id)

        # Проверяем, что текущий пользователь владелец файла
        if file_instance.user != request.user:
            return Response({"message": "You are not the owner of this file"}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные из запроса
        new_name = request.data.get('name')

        # Проверяем, что имя файла не пустое
        if not new_name:
            return Response({"message": "File name cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Обновляем имя файла
        file_instance.file.name = new_name
        file_instance.save()

        # Возвращаем успешный ответ
        return Response({"success": True, "message": "Renamed"}, status=status.HTTP_200_OK)


class FileDeleteView(DestroyAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class FileDownloadView(APIView):
    permission_classes = [IsOwnerOrReadOnly]  # Предполагается, что у вас есть соответствующие разрешения

    def get(self, request, file_id):
        # Получаем файл по его идентификатору, если он существует
        file_instance = get_object_or_404(File, id=file_id)

        if file_instance.user != request.user:
            return HttpResponseForbidden("You do not have permission to access this file.")

            # Отправка файла пользователю
        file_path = file_instance.file.path  # Путь к файлу
        file_name = file_instance.file.name  # Имя файла
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)


class FileAccessView(APIView):
    def post(self, request, file_id):
        # Проверяем, что текущий пользователь владелец файла
        if not File.objects.filter(id=file_id, user=request.user).exists():
            return Response({"detail": "You are not the owner of this file"}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные из запроса
        email = request.data.get('email')

        # Проверяем, что email не пустой
        if not email:
            return Response({"detail": "Email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Создаем новую запись о доступе к файлу
        file_access = FileAccess.objects.create(file_id=file_id, email=email)

        # Получаем всех пользователей, имеющих доступ к файлу
        accesses = FileAccess.objects.filter(file_id=file_id)
        serializer = FileAccessSerializer(accesses, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class FileAccessDeleteView(APIView):
    def delete(self, request, file_id):
        # Получаем пользователя из запроса
        user = request.user

        # Проверяем, что пользователь аутентифицирован
        if not user.is_authenticated:
            return Response({"detail": "You are not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        # Проверяем, что текущий пользователь владелец файла
        if not File.objects.filter(id=file_id, user=user).exists():
            return Response({"detail": "You are not the owner of this file"}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные из запроса
        email = request.data.get('email')

        # Проверяем, что email не пустой
        if not email:
            return Response({"detail": "Email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пользователь, которого пытаемся удалить, есть в списке соавторов файла
        if not FileAccess.objects.filter(file_id=file_id, email=email).exists():
            return Response({"detail": "User not found in the list of co-authors"}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, что пользователь не пытается удалить самого себя
        if user.email == email:
            return Response({"detail": "You cannot remove yourself from the list of co-authors"}, status=status.HTTP_403_FORBIDDEN)

        # Удаляем запись о доступе к файлу
        FileAccess.objects.filter(file_id=file_id, email=email).delete()

        # Получаем список всех пользователей, имеющих доступ к файлу
        accesses = FileAccess.objects.filter(file_id=file_id)
        serializer = FileAccessSerializer(accesses, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Получаем все файлы текущего пользователя
        user_files = File.objects.filter(user=request.user)

        # Сериализуем данные о файлах и их доступах
        data = []
        for file in user_files:
            file_data = {
                "file_id": file.file_id,
                "name": file.file.name,  # Имя файла, если хранится отдельно
                "url": file.file.url,  # URL для скачивания файла
                "accesses": []  # Доступы к файлу
            }
            # Получаем и добавляем доступы к файлу
            for access in file.accesses.all():
                access_data = {
                    "fullname": access.user.full_name,
                    "email": access.user.email,
                    "type": access.type
                }
                file_data["accesses"].append(access_data)
            data.append(file_data)

        return Response(data, status=status.HTTP_200_OK)


class SharedFilesView(APIView):
    def get(self, request):
        # Получаем список файлов, к которым имеет доступ пользователь, исключая файлы пользователя
        shared_files = File.objects.exclude(user=request.user)

        # Сериализуем данные о файлах для передачи в ответе
        serialized_files = []
        for file_obj in shared_files:
            file_data = {
                'file_id': file_obj.file_id,
                'name': file_obj.file.name,
                'url': file_obj.file.url,
            }
            serialized_files.append(file_data)

        return Response(serialized_files, status=status.HTTP_200_OK)
