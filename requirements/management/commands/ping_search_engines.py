import json
import ssl
import urllib.request
import urllib.error
from django.core.management.base import BaseCommand
from django.utils import timezone
from requirements.models import JobPosting, Category
from blog.models import BlogPost


class Command(BaseCommand):
    help = 'Notifies and pings search engines (IndexNow, Google, Bing) with all live URLs for instant indexing.'

    def handle(self, *args, **options):
        host = 'https://kashiiupdatez.online'
        key = '7e4c3a9d2b1f8e5a0c6d7b8a9e1f2c3d'
        key_location = f'{host}/{key}.txt'

        url_list = [
            f'{host}/',
            f'{host}/about/',
            f'{host}/contact/',
            f'{host}/privacy-policy/',
            f'{host}/terms/',
            f'{host}/disclaimer/',
            f'{host}/blog/',
            f'{host}/youtube/',
            f'{host}/debugger/',
            f'{host}/sql/',
            f'{host}/sitemap.xml',
            f'{host}/rss.xml',
        ]

        # Add categories
        for cat in Category.objects.all():
            url_list.append(f'{host}/category/{cat.slug}/')

        # Add active jobs
        for job in JobPosting.objects.filter(status="ACTIVE", deadline__gt=timezone.now())[:50]:
            url_list.append(f'{host}/category/{job.category.slug}/job/{job.uuid}/')

        # Add blog posts
        for post in BlogPost.objects.filter(is_published=True):
            url_list.append(f'{host}/blog/{post.slug}/')

        url_list = list(dict.fromkeys(url_list))
        self.stdout.write(self.style.NOTICE(f"🚀 Collected {len(url_list)} unique URLs for Search Engine Indexing submission..."))

        ssl_ctx = ssl._create_unverified_context()

        # 1. IndexNow API Submission (Bing, Yandex, Naver, Seznam)
        indexnow_payload = {
            "host": "kashiiupdatez.online",
            "key": key,
            "keyLocation": key_location,
            "urlList": url_list
        }

        try:
            req = urllib.request.Request(
                'https://api.indexnow.org/indexnow',
                data=json.dumps(indexnow_payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                    'User-Agent': 'KashiiUpdatez-SEO-Agent/1.0'
                }
            )
            with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as resp:
                self.stdout.write(self.style.SUCCESS(f"✅ [IndexNow Submission]: HTTP {resp.status} - {len(url_list)} URLs successfully submitted to Bing/IndexNow network!"))
        except urllib.error.HTTPError as e:
            self.stdout.write(self.style.WARNING(f"⚠️ [IndexNow Submission HTTP {e.code}]: {e.read().decode('utf-8', errors='ignore')}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ [IndexNow Submission Error]: {e}"))

        # 2. Ping Bing Sitemap Endpoint
        try:
            bing_ping = f"https://www.bing.com/ping?sitemap={host}/sitemap.xml"
            req = urllib.request.Request(bing_ping, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                self.stdout.write(self.style.SUCCESS(f"✅ [Bing Sitemap Ping]: HTTP {resp.status}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"ℹ️ [Bing Sitemap Ping]: {e}"))

        self.stdout.write(self.style.SUCCESS(f"🎉 Search Engine Ping Completed for Kashii Update ({len(url_list)} URLs)!"))
