from django.apps import AppConfig
from pathlib import Path


class RecommendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommend'

    def ready(self):
        """서버 기동 시 세션별 for_llm_* 파일 정리."""
        try:
            base_dir = Path(__file__).resolve().parent.parent  # Web/ 경로
            llm_dir = base_dir.parent / "ai" / "db"  # 프로젝트 루트 기준 ai/db
            if not llm_dir.exists():
                return

            # for_llm_{session_key}.json 파일만 정리 (공용 for_llm.json은 유지)
            for path in llm_dir.glob("for_llm_*.json"):
                try:
                    path.unlink()
                except Exception as e:  # noqa: BLE001
                    print(f"[recommend.apps] 파일 삭제 실패: {path} ({e})")
        except Exception as e:  # noqa: BLE001
            print(f"[recommend.apps] 초기 정리 중 오류: {e}")
