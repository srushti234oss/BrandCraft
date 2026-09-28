"""AI orchestration has no database models of its own.

The canonical Brand model lives in brands.models. Keeping only that model
prevents Django from proposing an unused second brand table.
"""
