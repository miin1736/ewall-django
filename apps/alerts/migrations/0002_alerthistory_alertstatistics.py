# Generated migration for AlertHistory and AlertStatistics models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0001_initial'),
    ]

    operations = [
        # EmailQueue에 alert 필드 추가
        migrations.AddField(
            model_name='emailqueue',
            name='alert',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='email_history',
                to='alerts.alert',
                verbose_name='알림'
            ),
        ),
        
        # EmailQueue reason choices 확장
        migrations.AlterField(
            model_name='emailqueue',
            name='reason',
            field=models.CharField(
                choices=[
                    ('price_drop', '가격 하락'),
                    ('restock', '재입고'),
                    ('price_spike', '가격 급등'),
                    ('trend_alert', '추세 알림'),
                ],
                max_length=50,
                verbose_name='알림 사유'
            ),
        ),
        
        # AlertHistory 모델 생성
        migrations.CreateModel(
            name='AlertHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('product_id', models.CharField(db_index=True, max_length=100, verbose_name='상품 ID')),
                ('product_data', models.JSONField(verbose_name='상품 스냅샷')),
                ('matched_conditions', models.JSONField(verbose_name='매칭된 조건')),
                ('priority', models.IntegerField(default=3, verbose_name='우선순위')),
                ('email_sent', models.BooleanField(default=False, verbose_name='이메일 발송 여부')),
                ('email_sent_at', models.DateTimeField(blank=True, null=True, verbose_name='발송 시각')),
                ('clicked', models.BooleanField(default=False, verbose_name='클릭 여부')),
                ('clicked_at', models.DateTimeField(blank=True, null=True, verbose_name='클릭 시각')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성일')),
                ('alert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='alerts.alert', verbose_name='알림')),
            ],
            options={
                'verbose_name': '알림 이력',
                'verbose_name_plural': '알림 이력',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['alert', 'created_at'], name='alerts_aler_alert_i_idx'),
                    models.Index(fields=['product_id', 'created_at'], name='alerts_aler_product_idx'),
                    models.Index(fields=['email_sent', 'created_at'], name='alerts_aler_email_s_idx'),
                ],
            },
        ),
        
        # AlertStatistics 모델 생성
        migrations.CreateModel(
            name='AlertStatistics',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField(db_index=True, verbose_name='날짜')),
                ('total_matched', models.IntegerField(default=0, verbose_name='매칭 수')),
                ('total_sent', models.IntegerField(default=0, verbose_name='발송 수')),
                ('total_clicked', models.IntegerField(default=0, verbose_name='클릭 수')),
                ('open_rate', models.FloatField(default=0.0, verbose_name='오픈율 (%)')),
                ('click_rate', models.FloatField(default=0.0, verbose_name='클릭율 (%)')),
                ('avg_matched_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='평균 매칭 가격')),
                ('avg_discount_rate', models.FloatField(blank=True, null=True, verbose_name='평균 할인율 (%)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('alert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statistics', to='alerts.alert', verbose_name='알림')),
            ],
            options={
                'verbose_name': '알림 통계',
                'verbose_name_plural': '알림 통계',
                'ordering': ['-date'],
                'unique_together': {('alert', 'date')},
                'indexes': [
                    models.Index(fields=['alert', 'date'], name='alerts_aler_alert_d_idx'),
                    models.Index(fields=['date'], name='alerts_aler_date_idx'),
                ],
            },
        ),
        
        # EmailQueue에 인덱스 추가
        migrations.AddIndex(
            model_name='emailqueue',
            index=models.Index(fields=['alert', 'created_at'], name='alerts_emai_alert_c_idx'),
        ),
    ]
