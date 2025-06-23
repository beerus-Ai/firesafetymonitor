import os
import logging
import googlemaps
from datetime import datetime
from app import app, db
from models import Alert

logger = logging.getLogger(__name__)

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

class GPSNavigator:
    def __init__(self):
        self.gmaps = None
        if GOOGLE_MAPS_API_KEY:
            try:
                self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
                logger.info("Google Maps client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Google Maps client: {e}")
        else:
            logger.warning("Google Maps API key not configured")
    
    def get_coordinates_from_address(self, address):
        """Convert address to latitude and longitude coordinates"""
        if not self.gmaps:
            logger.error("Google Maps client not available")
            return None, None
        
        try:
            geocode_result = self.gmaps.geocode(address)
            
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return location['lat'], location['lng']
            else:
                logger.warning(f"No results found for address: {address}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            return None, None
    
    def get_address_from_coordinates(self, latitude, longitude):
        """Convert latitude and longitude to address"""
        if not self.gmaps:
            logger.error("Google Maps client not available")
            return None
        
        try:
            reverse_geocode_result = self.gmaps.reverse_geocode((latitude, longitude))
            
            if reverse_geocode_result:
                return reverse_geocode_result[0]['formatted_address']
            else:
                logger.warning(f"No address found for coordinates: {latitude}, {longitude}")
                return None
                
        except Exception as e:
            logger.error(f"Error reverse geocoding coordinates ({latitude}, {longitude}): {e}")
            return None
    
    def get_route_to_location(self, origin, destination, mode='driving'):
        """Get driving directions from origin to destination"""
        if not self.gmaps:
            logger.error("Google Maps client not available")
            return None
        
        try:
            directions_result = self.gmaps.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                departure_time=datetime.now(),
                traffic_model='best_guess'
            )
            
            if directions_result:
                route = directions_result[0]
                return {
                    'duration': route['legs'][0]['duration']['text'],
                    'distance': route['legs'][0]['distance']['text'],
                    'duration_in_traffic': route['legs'][0].get('duration_in_traffic', {}).get('text'),
                    'start_address': route['legs'][0]['start_address'],
                    'end_address': route['legs'][0]['end_address'],
                    'steps': [
                        {
                            'instruction': step['html_instructions'],
                            'distance': step['distance']['text'],
                            'duration': step['duration']['text']
                        }
                        for step in route['legs'][0]['steps']
                    ],
                    'overview_polyline': route['overview_polyline']['points']
                }
            else:
                logger.warning(f"No route found from {origin} to {destination}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting route from {origin} to {destination}: {e}")
            return None
    
    def get_nearest_fire_stations(self, latitude, longitude, radius=10000):
        """Find nearest fire stations to a location"""
        if not self.gmaps:
            logger.error("Google Maps client not available")
            return []
        
        try:
            places_result = self.gmaps.places_nearby(
                location=(latitude, longitude),
                radius=radius,
                type='fire_station'
            )
            
            fire_stations = []
            for place in places_result.get('results', []):
                station_info = {
                    'name': place.get('name'),
                    'address': place.get('vicinity'),
                    'latitude': place['geometry']['location']['lat'],
                    'longitude': place['geometry']['location']['lng'],
                    'rating': place.get('rating'),
                    'place_id': place.get('place_id')
                }
                fire_stations.append(station_info)
            
            # Sort by distance (Google Places API returns them roughly in order)
            return fire_stations
            
        except Exception as e:
            logger.error(f"Error finding fire stations near ({latitude}, {longitude}): {e}")
            return []
    
    def calculate_distance_between_points(self, origin, destination):
        """Calculate distance and travel time between two points"""
        if not self.gmaps:
            logger.error("Google Maps client not available")
            return None
        
        try:
            distance_result = self.gmaps.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode='driving',
                units='metric',
                departure_time=datetime.now(),
                traffic_model='best_guess'
            )
            
            if distance_result['rows'][0]['elements'][0]['status'] == 'OK':
                element = distance_result['rows'][0]['elements'][0]
                return {
                    'distance': element['distance']['text'],
                    'distance_value': element['distance']['value'],  # in meters
                    'duration': element['duration']['text'],
                    'duration_value': element['duration']['value'],  # in seconds
                    'duration_in_traffic': element.get('duration_in_traffic', {}).get('text')
                }
            else:
                logger.warning(f"Could not calculate distance from {origin} to {destination}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating distance from {origin} to {destination}: {e}")
            return None
    
    def get_alert_navigation_info(self, alert_id, responder_location):
        """Get comprehensive navigation information for an alert"""
        try:
            with app.app_context():
                alert = Alert.query.get(alert_id)
                if not alert:
                    logger.error(f"Alert {alert_id} not found")
                    return None
                
                # Get alert location
                if alert.latitude and alert.longitude:
                    alert_location = (alert.latitude, alert.longitude)
                elif alert.address:
                    lat, lng = self.get_coordinates_from_address(alert.address)
                    if lat and lng:
                        alert_location = (lat, lng)
                        # Update alert with coordinates
                        alert.latitude = lat
                        alert.longitude = lng
                        db.session.commit()
                    else:
                        logger.error(f"Could not determine location for alert {alert_id}")
                        return None
                else:
                    logger.error(f"No location information available for alert {alert_id}")
                    return None
                
                # Get route to alert location
                route = self.get_route_to_location(responder_location, alert_location)
                
                # Find nearest fire stations
                fire_stations = self.get_nearest_fire_stations(
                    alert.latitude, alert.longitude
                )
                
                # Get route to nearest fire station
                fire_station_route = None
                if fire_stations:
                    nearest_station = fire_stations[0]
                    fire_station_route = self.get_route_to_location(
                        responder_location,
                        (nearest_station['latitude'], nearest_station['longitude'])
                    )
                
                return {
                    'alert': {
                        'id': alert.id,
                        'title': alert.title,
                        'severity': alert.severity,
                        'latitude': alert.latitude,
                        'longitude': alert.longitude,
                        'address': alert.address or self.get_address_from_coordinates(
                            alert.latitude, alert.longitude
                        )
                    },
                    'route_to_alert': route,
                    'nearest_fire_stations': fire_stations,
                    'route_to_fire_station': fire_station_route
                }
                
        except Exception as e:
            logger.error(f"Error getting navigation info for alert {alert_id}: {e}")
            return None

# Global GPS navigator instance
gps_navigator = GPSNavigator()

def get_navigation_to_alert(alert_id, responder_location):
    """Get navigation information for an alert"""
    return gps_navigator.get_alert_navigation_info(alert_id, responder_location)

def geocode_address(address):
    """Convert address to coordinates"""
    return gps_navigator.get_coordinates_from_address(address)

def reverse_geocode(latitude, longitude):
    """Convert coordinates to address"""
    return gps_navigator.get_address_from_coordinates(latitude, longitude)

def find_fire_stations(latitude, longitude):
    """Find fire stations near a location"""
    return gps_navigator.get_nearest_fire_stations(latitude, longitude)
