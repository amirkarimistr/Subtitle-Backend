from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import request_sub as subscene


class SearchSubtitle(APIView):

    def get(self, request, format=None):
        try:
            method = request.GET['method']
            q = request.GET['q']

            if method == 'search':
                # Search for subtitle
                sel_title = subscene.sel_title(q)
                if sel_title != -1:
                    return Response({'status': True, 'result': sel_title}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': False, 'error': "Sorry, the subtitles for this media file aren't available."})
        except:
            return Response({'status': False}, status= status.HTTP_500_INTERNAL_SERVER_ERROR)
