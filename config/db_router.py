"""Database Router for Read Replicas"""

class ReadReplicaRouter:
    """읽기/쓰기 분리 라우터"""
    
    def db_for_read(self, model, **hints):
        """읽기는 replica로"""
        if model._meta.app_label in ['sessions', 'admin']:
            return 'default'
        from django.conf import settings
        return 'replica' if 'replica' in settings.DATABASES else 'default'
    
    def db_for_write(self, model, **hints):
        """쓰기는 항상 primary로"""
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """모든 관계 허용"""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """마이그레이션은 primary만"""
        return db == 'default'
