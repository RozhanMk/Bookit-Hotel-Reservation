from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class ReservationViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]

    def list(self, request):
        pass

    def retrieve(self, request):
        pass

    def partial_update(self, request):
        pass

    def destroy(self, request):
        pass

    def create(self, request):
        pass