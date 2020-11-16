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
                    error_message = "Sorry, the subtitles for this media file aren't available."
                    return Response({'status': False, 'error': error_message}, status=status.HTTP_404_NOT_FOUND)
            elif method == 'getsubs':
                subtitles = subscene.sel_sub(q)
                return Response({'statuss': True, 'result': subtitles})


        except:
            return Response({'status': False}, status= status.HTTP_500_INTERNAL_SERVER_ERROR)
