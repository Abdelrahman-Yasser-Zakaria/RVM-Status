from rest_framework.routers import DefaultRouter
from .views import RVMViewSet

router = DefaultRouter()
router.register("rvms", RVMViewSet, basename="rvms")

urlpatterns = router.urls
