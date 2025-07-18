import os

from django.db import IntegrityError
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated

from bookit import settings
from hotel.models import Hotel, HotelFacility, Facility
from hotelManager.models import HotelManager
from hotel.serializers import HotelSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class HotelViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('List of all accepted hotels', HotelSerializer(many=True)),
            404: 'No hotels found'
        },
        operation_description="List all hotels with status 'Accepted'.",
        tags=['Hotel']
    )
    def list(self, request):
        """it lists all the hotels"""
        hotels = Hotel.objects.filter(status="Accepted")
        if not hotels:
            return Response({"error": "hotel not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = HotelSerializer(hotels, many=True, context={'request': request})
        return Response({'data':serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('List of hotels managed by the current user', HotelSerializer(many=True)),
        },
        operation_description="List all hotels owned by the authenticated hotel manager.",
        tags=['Hotel']
    )
    @action(detail=False, methods=['get'], url_path='my-hotels')
    def my_hotels(self, request):
        hotels = Hotel.objects.filter(hotel_manager__user=request.user)
        serializer = HotelSerializer(hotels, many=True, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response('Hotel details retrieved successfully', HotelSerializer),
            404: 'Hotel not found'
        },
        operation_description="Retrieve a single hotel by its ID, owned by the current user.",
        tags=['Hotel']
    )
    def retrieve(self, request, pk=None):
        """Retrieve a single hotel by its pk, owned by the current user"""
        hotel = get_object_or_404(Hotel, pk=pk, hotel_manager__user=request.user)
        serializer = HotelSerializer(hotel, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=HotelSerializer,
        responses={
            200: openapi.Response('Hotel updated successfully', HotelSerializer),
            400: 'Bad Request',
            404: 'Hotel not found'
        },
        operation_description="Partially update a hotel by its ID.",
        tags=['Hotel']
    )
    def partial_update(self, request, pk=None):
        """Partially update hotel info by pk"""
        hotel = get_object_or_404(Hotel, pk=pk, hotel_manager__user=request.user)
        data = request.data.copy()
        
        # Handle facilities if present in the request
        if 'facilities' in data:
            try:
                # Clear existing facilities
                hotel.facilities.clear()
                
                # Add new facilities
                facilities = data.get('facilities').split(",")
                for facility_name in facilities:
                    try:
                        facility = HotelFacility.objects.get(facility_type=facility_name.strip())
                        hotel.facilities.add(facility)
                    except HotelFacility.DoesNotExist:
                        continue
                
                # Remove facilities from data to avoid serializer issues
                del data['facilities']
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
        serializer = HotelSerializer(hotel, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            try:
                # Handle file uploads similar to create method
                files_list = {
                    "image": [settings.MEDIA_ROOT + "/hotel/images/", 'image'],
                    "hotel_license": [settings.MEDIA_ROOT + "/hotel/licenses/", 'license']
                }
    
                for field in files_list.keys():
                    if field in request.FILES:
                        file = request.FILES[field]
                        upload_path = files_list[field][0]
                        file_extension = os.path.splitext(file.name)[1]
                        file_name = f"hotel_{hotel.id}_{field}{file_extension}"
    
                        if os.path.exists(os.path.join(upload_path, file_name)):
                            os.remove(os.path.join(upload_path, file_name))
    
                        file.name = file_name
                        setattr(hotel, field, file)
    
                serializer.save()
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            204: 'Hotel deleted successfully',
            404: 'Hotel not found'
        },
        operation_description="Delete a hotel by its ID.",
        tags=['Hotel']
    )
    def destroy(self, request, pk=None):
        """Delete a hotel by pk if owned by current user"""
        hotel = get_object_or_404(Hotel, pk=pk, hotel_manager__user=request.user)
        hotel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        request_body=HotelSerializer,
        responses={
            201: openapi.Response('Hotel created successfully', HotelSerializer),
            400: 'Bad Request'
        },
        operation_description="Create a new hotel associated with the authenticated hotel manager.",
        tags=['Hotel']
    )
    def create(self, request):
        """Creates a new hotel for the authenticated hotel_manager with facilities"""
        try:
            hotel_manager = HotelManager.objects.get(user=request.user)
        except HotelManager.DoesNotExist:
            return Response({"error": "Hotel manager not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        try:
            files_list = {
                "image": [settings.MEDIA_ROOT + "/hotel/images/", 'image'],
                "hotel_license": [settings.MEDIA_ROOT + "/hotel/licenses/", 'license']
            }

            hotel = Hotel.objects.create(
                hotel_manager=hotel_manager,
                name=data.get('name'),
                location=data.get('location'),
                description=data.get('description'),
                hotel_iban_number=data.get('hotel_iban_number', ''),
                status=data.get('status', 'Pending'),
                discount=data.get('discount', 0),
                discount_status=data.get('discount_status', 'Inactive')
            )

            for field in files_list.keys():
                if field in request.FILES:
                    file = request.FILES[field]
                    upload_path = files_list[field][0]
                    file_extension = os.path.splitext(file.name)[1]
                    file_name = f"hotel_{hotel.id}_{field}{file_extension}"

                    if os.path.exists(os.path.join(upload_path, file_name)):
                        os.remove(os.path.join(upload_path, file_name))

                    file.name = file_name
                    setattr(hotel, field, file)

            facilities = data.get('facilities').split(",")
            for facility_name in facilities:
                try:
                    facility = HotelFacility.objects.get(facility_type=facility_name)
                    hotel.facilities.add(facility)
                except HotelFacility.DoesNotExist:
                    continue

            hotel.save()

            serializer = HotelSerializer(hotel)
            return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            return Response({"error": "A hotel with the provided information already exists."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('location', openapi.IN_QUERY, description="Location to filter hotels", type=openapi.TYPE_STRING)
        ],
        responses={200: openapi.Response('Hotels filtered by location', HotelSerializer(many=True))},
        operation_description="List all accepted hotels filtered by location.",
        tags=['Hotel']
    )
    @action(detail=False, methods=['get'], url_path='by-location')
    def hotels_by_location(self, request):
        location = request.query_params.get('location')
        if not location:
            return Response({'error': 'Location query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        hotels = Hotel.objects.filter(location__iexact=location, status="Accepted")
        serializer = HotelSerializer(hotels, many=True, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        responses={200: openapi.Response('Hotels with discount', HotelSerializer(many=True))},
        operation_description="List all accepted hotels that have a discount.",
        tags=['Hotel']
    )
    @action(detail=False, methods=['get'], url_path='with-discount')
    def hotels_with_discount(self, request):
        hotels = Hotel.objects.filter(discount__gt=0, status="Accepted")
        serializer = HotelSerializer(hotels, many=True, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        responses={200: openapi.Response('Hotels with rating > 4.5', HotelSerializer(many=True))},
        operation_description="List all accepted hotels with a rating greater than 4.5.",
        tags=['Hotel']
    )
    @action(detail=False, methods=['get'], url_path='top-rated')
    def top_rated_hotels(self, request):
        hotels = Hotel.objects.filter(rate__gt=4.5, status="Accepted")
        serializer = HotelSerializer(hotels, many=True, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class FacilitySeederViewSet (viewsets.ViewSet):

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Facility name'),
            },
        ),
        responses={
            201: openapi.Response('Facilities created successfully', 
                                  schema=openapi.Schema(type=openapi.TYPE_STRING, description='ok')),
            400: 'Bad Request'
        },
        operation_description="Seed multiple predefined facilities into the database.",
        tags=['Facility']
    )
    def create_fac(self, request):
        try:
            data = request.data
            name = data['name']
            facilities = [
                "WIFI", "PARKING", "restaurant", "coffeShop", "roomService",
                "laundryService", "supportAgent", "elevator", "safeBox",
                "tv", "freeBreakFast", "meetingRoom", "childCare", "POOL",
                "GYM", "taxi", "pets_allowed", "shoppingMall"
            ]
            for fa in facilities:
                if hasattr(Facility, fa):
                    HotelFacility.objects.get_or_create(facility_type=getattr(Facility, fa))

            return Response({'data':'ok'},status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

