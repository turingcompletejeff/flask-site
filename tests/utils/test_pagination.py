"""
Comprehensive test suite for pagination utility.

Tests the paginate_query() function with comprehensive coverage of:
- Basic pagination scenarios (first, middle, last pages)
- Edge cases (invalid page numbers, boundary conditions)
- Custom per_page values
- Return value validation and tuple structure
- Pagination flags (has_prev, has_next)

Target: 95%+ coverage of app/utils/pagination.py (39 lines)
"""

import pytest
from app.models import User
from app.utils.pagination import paginate_query


class TestPaginateQueryBasic:
    """Tests for basic pagination functionality across pages."""

    def test_first_page_of_multi_page_results(self, db):
        """
        Test paginating the first page when multiple pages exist.

        Scenario: 35 items with per_page=10 (4 pages total)
        Verify: Items 1-10 returned, has_prev=False, has_next=True
        """
        # Arrange: Create 35 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(35)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 10
        assert items[0].username == 'user000'
        assert items[-1].username == 'user009'
        assert total_pages == 4
        assert current_page == 1
        assert has_prev is False
        assert has_next is True

    def test_middle_page_of_multi_page_results(self, db):
        """
        Test paginating a middle page when multiple pages exist.

        Scenario: 35 items with per_page=10, requesting page 2
        Verify: Items 11-20 returned, has_prev=True, has_next=True
        """
        # Arrange: Create 35 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(35)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=2, per_page=10
        )

        # Assert
        assert len(items) == 10
        assert items[0].username == 'user010'
        assert items[-1].username == 'user019'
        assert total_pages == 4
        assert current_page == 2
        assert has_prev is True
        assert has_next is True

    def test_last_page_of_multi_page_results(self, db):
        """
        Test paginating the last page when multiple pages exist.

        Scenario: 35 items with per_page=10, requesting page 4 (last)
        Verify: Items 31-35 returned (5 items), has_prev=True, has_next=False
        """
        # Arrange: Create 35 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(35)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=4, per_page=10
        )

        # Assert
        assert len(items) == 5
        assert items[0].username == 'user030'
        assert items[-1].username == 'user034'
        assert total_pages == 4
        assert current_page == 4
        assert has_prev is True
        assert has_next is False

    def test_single_page_total_items_less_than_per_page(self, db):
        """
        Test pagination when total items fit on a single page.

        Scenario: 8 items with per_page=10
        Verify: All 8 items on page 1, has_prev=False, has_next=False
        """
        # Arrange: Create 8 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(8)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 8
        assert total_pages == 1
        assert current_page == 1
        assert has_prev is False
        assert has_next is False

    def test_empty_query_no_items(self, db):
        """
        Test pagination on an empty query (0 items).

        Scenario: 0 items in database
        Verify: Empty list returned, total_pages=0
        """
        # Arrange: No users created
        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 0
        assert items == []
        assert total_pages == 0
        assert current_page == 1
        assert has_prev is False
        assert has_next is False


class TestPaginateQueryPageNumberEdgeCases:
    """Tests for edge cases and boundary conditions with page numbers."""

    def test_page_less_than_one_defaults_to_page_one(self, db):
        """
        Test that requesting page < 1 defaults to page 1.

        Scenario: 25 items with per_page=10, request page=-5
        Verify: Clamped to page 1, returns items 1-10
        """
        # Arrange: Create 25 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(25)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=-5, per_page=10
        )

        # Assert
        assert current_page == 1
        assert len(items) == 10
        assert items[0].username == 'user000'
        assert has_prev is False

    def test_page_zero_defaults_to_page_one(self, db):
        """
        Test that requesting page=0 defaults to page 1.

        Scenario: 25 items with per_page=10, request page=0
        Verify: Clamped to page 1, returns items 1-10
        """
        # Arrange: Create 25 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(25)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=0, per_page=10
        )

        # Assert
        assert current_page == 1
        assert len(items) == 10
        assert items[0].username == 'user000'

    def test_page_greater_than_total_pages_clamps_to_last_page(self, db):
        """
        Test that requesting page > total_pages clamps to last page.

        Scenario: 25 items with per_page=10 (3 pages), request page=99
        Verify: Clamped to page 3, returns items 21-25
        """
        # Arrange: Create 25 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(25)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=99, per_page=10
        )

        # Assert
        assert total_pages == 3
        assert current_page == 3
        assert len(items) == 5
        assert items[0].username == 'user020'
        assert items[-1].username == 'user024'
        assert has_next is False

    def test_page_one_with_exactly_per_page_items(self, db):
        """
        Test page 1 when total items equals exactly per_page (1 full page).

        Scenario: 10 items with per_page=10
        Verify: Page 1 with all 10 items, total_pages=1, has_next=False
        """
        # Arrange: Create exactly 10 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(10)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 10
        assert total_pages == 1
        assert current_page == 1
        assert has_prev is False
        assert has_next is False

    def test_page_two_with_exactly_two_per_page_items(self, db):
        """
        Test page 2 when total items equals exactly 2*per_page (2 full pages).

        Scenario: 20 items with per_page=10, request page=2
        Verify: Page 2 with items 11-20, total_pages=2, has_prev=True, has_next=False
        """
        # Arrange: Create exactly 20 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(20)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=2, per_page=10
        )

        # Assert
        assert len(items) == 10
        assert items[0].username == 'user010'
        assert total_pages == 2
        assert current_page == 2
        assert has_prev is True
        assert has_next is False


class TestPaginateQueryItemsCountEdgeCases:
    """Tests for edge cases related to item counts and page boundaries."""

    def test_exactly_per_page_items_single_full_page(self, db):
        """
        Test with exactly per_page items (creates one full page).

        Scenario: 10 items with per_page=10
        Verify: Single page returned completely
        """
        # Arrange: Create exactly 10 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(10)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 10
        assert total_pages == 1

    def test_per_page_plus_one_items_creates_two_pages(self, db):
        """
        Test with per_page + 1 items (creates 2 pages).

        Scenario: 11 items with per_page=10
        Verify: Page 1 has 10 items, total_pages=2
        """
        # Arrange: Create 11 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(11)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 10
        assert total_pages == 2
        assert has_next is True

    def test_per_page_minus_one_items_single_page(self, db):
        """
        Test with per_page - 1 items (single page).

        Scenario: 9 items with per_page=10
        Verify: All items on page 1, total_pages=1
        """
        # Arrange: Create 9 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(9)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 9
        assert total_pages == 1

    def test_odd_number_of_items_across_pages(self, db):
        """
        Test with odd number of items distributed across multiple pages.

        Scenario: 27 items with per_page=10 (3 pages: 10, 10, 7)
        Verify: Page 3 has 7 items, total_pages=3
        """
        # Arrange: Create 27 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(27)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=3, per_page=10
        )

        # Assert
        assert len(items) == 7
        assert total_pages == 3
        assert items[0].username == 'user020'
        assert items[-1].username == 'user026'


class TestPaginateQueryPaginationFlags:
    """Tests for pagination navigation flags (has_prev, has_next)."""

    def test_has_prev_false_on_first_page(self, db):
        """
        Test that has_prev=False on first page.

        Scenario: 30 items, page 1
        Verify: has_prev is False
        """
        # Arrange: Create 30 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(30)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert has_prev is False

    def test_has_prev_true_on_second_page(self, db):
        """
        Test that has_prev=True on second page.

        Scenario: 30 items, page 2
        Verify: has_prev is True
        """
        # Arrange: Create 30 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(30)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=2, per_page=10
        )

        # Assert
        assert has_prev is True

    def test_has_next_false_on_last_page(self, db):
        """
        Test that has_next=False on last page.

        Scenario: 30 items (3 pages), page 3
        Verify: has_next is False
        """
        # Arrange: Create 30 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(30)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=3, per_page=10
        )

        # Assert
        assert has_next is False

    def test_has_next_true_on_first_page_with_multiple_pages(self, db):
        """
        Test that has_next=True on first page when multiple pages exist.

        Scenario: 30 items (3 pages), page 1
        Verify: has_next is True
        """
        # Arrange: Create 30 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(30)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert has_next is True

    def test_has_prev_and_has_next_both_false_on_single_page(self, db):
        """
        Test that has_prev=False and has_next=False on a single page result.

        Scenario: 5 items with per_page=10 (single page)
        Verify: Both flags are False
        """
        # Arrange: Create 5 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(5)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert has_prev is False
        assert has_next is False


class TestPaginateQueryCustomPerPageValues:
    """Tests for custom per_page values."""

    def test_per_page_five_smaller_pages(self, db):
        """
        Test pagination with per_page=5 (smaller pages).

        Scenario: 25 items with per_page=5
        Verify: Page 1 has 5 items, total_pages=5
        """
        # Arrange: Create 25 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(25)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=5
        )

        # Assert
        assert len(items) == 5
        assert total_pages == 5
        assert items[0].username == 'user000'
        assert items[-1].username == 'user004'

    def test_per_page_twenty_larger_pages(self, db):
        """
        Test pagination with per_page=20 (larger pages).

        Scenario: 50 items with per_page=20
        Verify: Page 1 has 20 items, total_pages=3
        """
        # Arrange: Create 50 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(50)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=20
        )

        # Assert
        assert len(items) == 20
        assert total_pages == 3
        assert items[0].username == 'user000'
        assert items[-1].username == 'user019'

    def test_per_page_one_one_item_per_page(self, db):
        """
        Test pagination with per_page=1 (one item per page).

        Scenario: 5 items with per_page=1
        Verify: Page 1 has 1 item, total_pages=5
        """
        # Arrange: Create 5 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(5)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=1
        )

        # Assert
        assert len(items) == 1
        assert total_pages == 5
        assert items[0].username == 'user000'

    def test_per_page_one_page_three(self, db):
        """
        Test page 3 with per_page=1 (one item per page).

        Scenario: 5 items with per_page=1, request page=3
        Verify: Page 3 has 1 item (user003), has_prev=True, has_next=True
        """
        # Arrange: Create 5 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(5)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=3, per_page=1
        )

        # Assert
        assert len(items) == 1
        assert items[0].username == 'user002'
        assert total_pages == 5
        assert current_page == 3
        assert has_prev is True
        assert has_next is True


class TestPaginateQueryReturnValue:
    """Tests for return value structure and validation."""

    def test_return_tuple_has_five_elements(self, db):
        """
        Test that return value is a tuple with exactly 5 elements.

        Scenario: Basic pagination query
        Verify: Tuple structure (items, total_pages, current_page, has_prev, has_next)
        """
        # Arrange: Create 10 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(10)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        result = paginate_query(query, page=1, per_page=10)

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 5

    def test_items_element_is_list(self, db):
        """
        Test that items element is a list.

        Scenario: Basic pagination query
        Verify: First element is a list
        """
        # Arrange: Create 10 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(10)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert isinstance(items, list)

    def test_total_pages_calculation_accuracy(self, db):
        """
        Test that total_pages is calculated correctly using ceiling division.

        Scenario: Various item counts
        Verify: total_pages = ceil(total_items / per_page)
        """
        # Test cases: (total_items, per_page, expected_total_pages)
        test_cases = [
            (0, 10, 0),    # 0 items
            (1, 10, 1),    # 1 item
            (10, 10, 1),   # exactly 1 page
            (11, 10, 2),   # 1 full page + 1 item
            (19, 10, 2),   # 1 full page + 9 items
            (20, 10, 2),   # exactly 2 pages
            (21, 10, 3),   # 2 full pages + 1 item
            (25, 5, 5),    # exactly 5 pages with per_page=5
            (26, 5, 6),    # 5 full pages + 1 item with per_page=5
        ]

        for total_items, per_page, expected_pages in test_cases:
            # Arrange
            # Clear previous users
            User.query.delete()

            users = [
                User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
                for i in range(total_items)
            ]
            for user in users:
                user.set_password('password123')
            db.session.add_all(users)
            db.session.commit()

            query = User.query.order_by(User.id)

            # Act
            items, total_pages, current_page, has_prev, has_next = paginate_query(
                query, page=1, per_page=per_page
            )

            # Assert
            assert total_pages == expected_pages, \
                f"Expected {expected_pages} pages for {total_items} items with per_page={per_page}, got {total_pages}"

    def test_current_page_reflects_input_or_clamped_value(self, db):
        """
        Test that current_page reflects the requested page or clamped value.

        Scenario: Various page requests
        Verify: current_page matches request (or clamped value)
        """
        # Arrange: Create 30 users (3 pages with per_page=10)
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(30)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Test cases: (requested_page, expected_current_page)
        test_cases = [
            (-5, 1),    # Negative page -> clamped to 1
            (0, 1),     # Page 0 -> clamped to 1
            (1, 1),     # Valid page 1
            (2, 2),     # Valid page 2
            (3, 3),     # Valid page 3 (last)
            (99, 3),    # Beyond last page -> clamped to 3
        ]

        for requested_page, expected_page in test_cases:
            # Act
            items, total_pages, current_page, has_prev, has_next = paginate_query(
                query, page=requested_page, per_page=10
            )

            # Assert
            assert current_page == expected_page, \
                f"Expected page {expected_page} for request page={requested_page}, got {current_page}"

    def test_return_items_are_user_objects(self, db):
        """
        Test that returned items are actual User model instances.

        Scenario: Basic pagination query
        Verify: Items are User objects with expected attributes
        """
        # Arrange: Create 3 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(3)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert len(items) == 3
        for item in items:
            assert isinstance(item, User)
            assert hasattr(item, 'username')
            assert hasattr(item, 'email')

    def test_flags_are_boolean_values(self, db):
        """
        Test that has_prev and has_next are boolean values.

        Scenario: Basic pagination query
        Verify: Both flags are bool type
        """
        # Arrange: Create 10 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(10)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert isinstance(has_prev, bool)
        assert isinstance(has_next, bool)


class TestPaginateQueryOffsetCalculation:
    """Tests for correct offset and limit application to SQLAlchemy queries."""

    def test_query_limit_and_offset_application(self, db):
        """
        Test that limit() and offset() are correctly applied to query.

        Scenario: Page 2 with per_page=10 should use offset=10, limit=10
        Verify: Correct items returned (11-20)
        """
        # Arrange: Create 30 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(30)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act: Request page 2 with per_page=10
        # offset = (2-1) * 10 = 10
        # Should skip first 10, get next 10
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=2, per_page=10
        )

        # Assert
        assert len(items) == 10
        assert items[0].username == 'user010'
        assert items[-1].username == 'user019'

    def test_offset_zero_for_first_page(self, db):
        """
        Test that first page uses offset=0.

        Scenario: Page 1 should use offset=0
        Verify: Gets items starting from first
        """
        # Arrange: Create 20 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(20)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=1, per_page=10
        )

        # Assert
        assert items[0].username == 'user000'

    def test_offset_calculation_page_three(self, db):
        """
        Test offset calculation for page 3.

        Scenario: Page 3 with per_page=5
        Verify: offset = (3-1) * 5 = 10, gets items 11-15
        """
        # Arrange: Create 20 users
        users = [
            User(username=f'user{i:03d}', email=f'user{i:03d}@test.com')
            for i in range(20)
        ]
        for user in users:
            user.set_password('password123')
        db.session.add_all(users)
        db.session.commit()

        query = User.query.order_by(User.id)

        # Act: Page 3, per_page=5
        # offset = (3-1) * 5 = 10
        items, total_pages, current_page, has_prev, has_next = paginate_query(
            query, page=3, per_page=5
        )

        # Assert
        assert len(items) == 5
        assert items[0].username == 'user010'
        assert items[-1].username == 'user014'
