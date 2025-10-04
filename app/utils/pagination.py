"""
Pagination helper utilities for the Flask application.
"""

def paginate_query(query, page, per_page=10):
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        page: Current page number (1-indexed)
        per_page: Number of items per page (default 10)

    Returns:
        tuple: (items, total_pages, current_page, has_prev, has_next)
    """
    # Handle invalid page numbers
    if page < 1:
        page = 1

    # Get total count
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division

    # Handle page beyond total pages
    if page > total_pages and total_pages > 0:
        page = total_pages

    # Calculate offset
    offset = (page - 1) * per_page

    # Get paginated items
    items = query.limit(per_page).offset(offset).all()

    # Calculate pagination info
    has_prev = page > 1
    has_next = page < total_pages

    return items, total_pages, page, has_prev, has_next
