from django.urls import path
from .views import (
    AuthorizationAPIView, RegisterAPIView,
    LogoutAPIView,
    FileUploadView, FileEditView, FileDeleteView,
    FileDownloadView, FileAccessView,
    FileAccessDeleteView, UserFilesView, SharedFilesView,

)

urlpatterns = [
    path('registration', RegisterAPIView.as_view(), name='registration'),
    path('authorization', AuthorizationAPIView.as_view(), name='authorization'),
    path('logout', LogoutAPIView.as_view(), name='logout'),
    path('files', FileUploadView.as_view(), name='file_upload'),
    path('files/<int:file_id>', FileEditView.as_view(), name='file-edit'),
    path('files/<int:pk>/delete', FileDeleteView.as_view(), name='file-delete'),
    path('files/<int:file_id>/download', FileDownloadView.as_view(), name='file-download'),
    path('files/<int:file_id>/accesses', FileAccessView.as_view(), name='file-accesses'),
    path('files/<int:file_id>/accesses', FileAccessDeleteView.as_view(), name='delete_file_access'),
    path('files/disk', UserFilesView.as_view(), name='user_files'),
    path('shared', SharedFilesView.as_view(), name='shared_files'),
]
