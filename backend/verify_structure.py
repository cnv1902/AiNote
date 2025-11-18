"""
Script to verify the new structure imports correctly.
Run this to check if the refactoring was successful.
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("🔍 Verifying new backend structure...\n")

try:
    # Test core imports
    print("✓ Testing core imports...")
    from app.core.config import settings
    from app.core.database import get_db, Base, engine
    from app.core.security import hash_password, verify_password, create_access_token
    from app.core.fts import install_notes_fts, install_ocr_fts
    from app.core.utils import hash_text_sha256
    print("  ✅ Core layer OK\n")

    # Test models
    print("✓ Testing models...")
    from app.models import User, Note, File, AuthRefreshToken
    print("  ✅ Models OK\n")

    # Test schemas
    print("✓ Testing schemas...")
    from app.schemas import UserCreate, UserOut, TokenPair, NoteCreate, NoteOut
    print("  ✅ Schemas OK\n")

    # Test CRUD
    print("✓ Testing CRUD layer...")
    from app.crud.user import get_user_by_email, create_user
    from app.crud.note import get_user_notes, create_note
    from app.crud.file import create_file, create_image_metadata
    from app.crud.auth import create_refresh_token, get_valid_refresh_token
    print("  ✅ CRUD layer OK\n")

    # Test services
    print("✓ Testing services layer...")
    from app.services.storage import storage_service
    from app.services.image import image_service
    from app.services.ocr import ocr_service
    from app.services.llm import llm_service
    print("  ✅ Services layer OK\n")

    # Test API
    print("✓ Testing API layer...")
    from app.api.dependencies import get_current_user
    from app.api.v1.auth import router as auth_router
    from app.api.v1.notes import router as notes_router
    print("  ✅ API layer OK\n")

    # Test main app
    print("✓ Testing main application...")
    from app.main import app, create_app
    print("  ✅ Main application OK\n")

    print("=" * 50)
    print("🎉 SUCCESS! All imports are working correctly!")
    print("=" * 50)
    print("\n📝 Next steps:")
    print("1. Run the application: uvicorn app.main:app --reload")
    print("2. Test the endpoints at http://localhost:8000/docs")
    print("3. If everything works, clean up old files using MIGRATION_CLEANUP.md")
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("\nPlease check the file structure and fix the import issue.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)
