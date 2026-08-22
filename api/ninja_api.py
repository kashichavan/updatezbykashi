from ninja import NinjaAPI
from api.routers.blog import router as blog_router
from api.routers.curriculum_js import router as curriculum_js_router
from api.routers.overview import router as overview_router

# Initialize production-grade Django Ninja OpenAPI instance
api = NinjaAPI(
    title="⚡ Kashii DevAcademy & Engineering Blog API",
    version="1.0.0",
    description="""
# 🚀 High-Performance Enterprise Backend API

Powered by **Django Ninja & Pydantic v2**, this OpenAPI suite provides type-safe endpoints for:
1. **📰 Technical Blog & Engineering Articles**: Categories, tags, Markdown/HTML articles, reading time metrics, view tracking, and related posts.
2. **⚡ JavaScript ES6+ Masterclass**: Complete 15 interactive chapters with V8 AST execution models, mental models, progressive code snippets, quizzes, debug challenges, interview questions, and curated video masterclasses.
3. **🔍 Live Code Step Execution**: AST Line-by-line execution tracer for interactive web IDEs and debuggers.
4. **🛣️ Curriculum Roadmaps & Platform Metrics**: Structured 7-stage learning journey and global DevAcademy stats.

### Interactive Documentation:
- **Swagger UI**: `/api/v1/docs`
- **Redoc**: `/api/v1/redoc`
- **OpenAPI Schema**: `/api/v1/openapi.json`
    """,
    docs_url="/docs",
    openapi_url="/openapi.json",
    docs_decorator=None,
)

# Register Sub-Routers
api.add_router("/blog", blog_router)
api.add_router("/curriculum/javascript", curriculum_js_router)
api.add_router("/curriculum", overview_router)
