"""
Comprehensive Multi-Language Learning Curriculum (Python 3, Java 17, JavaScript ES6+)
Unifies all 45 topics across Python, Java, and JavaScript with complete 22-section lessons.
"""
from .curriculum_python import PYTHON_TOPICS
from .curriculum_java import JAVA_TOPICS
from .curriculum_js import JS_TOPICS

CURRICULUM = {
    'python': {
        'title': 'Python 3 Complete Programming Academy',
        'short_title': 'Python 3',
        'icon': '🐍',
        'color': '#3b82f6',
        'badge': 'Dynamic & High-Level',
        'summary': 'The definitive complete Python 3 masterclass from basic syntax to advanced metaprogramming, OOP, and asynchronous generators.',
        'topics': PYTHON_TOPICS
    },
    'java': {
        'title': 'Java 17 Complete Enterprise Academy',
        'short_title': 'Java 17',
        'icon': '☕',
        'color': '#ea580c',
        'badge': 'Static, Typed & JVM',
        'summary': 'The definitive complete Java 17 enterprise academy covering JVM memory models, OOP architectures, Collections, and Multi-Threading.',
        'topics': JAVA_TOPICS
    },
    'javascript': {
        'title': 'Modern JavaScript (ES6+) Complete Academy',
        'short_title': 'JavaScript',
        'icon': '⚡',
        'color': '#eab308',
        'badge': 'Asynchronous & Event-Driven',
        'summary': 'The definitive complete Modern JavaScript ES6+ curriculum covering scope, arrow pipelines, async/await, closures, and the browser event loop.',
        'topics': JS_TOPICS
    }
}
