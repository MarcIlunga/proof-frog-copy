import pytest
from proof_frog import visitors, frog_parser, frog_ast


@pytest.mark.parametrize(
    "method,expected",
    [
        # Basic case: Two consecutive if statements with b and !b having identical blocks
        (
            """
            Bool? f(Bool b) {
                if (b) {
                    return None;
                }
                if (!b) {
                    return None;
                }
                return true;
            }
            """,
            """
            Bool? f(Bool b) {
                return None;
                return true;
            }
            """,
        ),
        # Basic case: Two exhaustive conditions with more complex blocks
        (
            """
            Int f(Bool b) {
                Int x = 1;
                if (b) {
                    x = 2;
                    return x;
                }
                if (!b) {
                    x = 2;
                    return x;
                }
                return x;
            }
            """,
            """
            Int f(Bool b) {
                Int x = 1;
                x = 2;
                return x;
                return x;
            }
            """,
        ),
        # Edge case: More complex complementary conditions (not syntactically obvious)
        (
            """
            Int f(Int n) {
                if (n > 0) {
                    return 1;
                }
                if (n <= 0) {
                    return 1;
                }
                return 0;
            }
            """,
            """
            Int f(Int n) {
                return 1;
                return 0;
            }
            """,
        ),
        # Edge case: Single if statement with else - should not be transformed
        (
            """
            Int f(Bool b) {
                if (b) {
                    return 1;
                } else {
                    return 1;
                }
                return 0;
            }
            """,
            """
            Int f(Bool b) {
                if (b) {
                    return 1;
                } else {
                    return 1;
                }
                return 0;
            }
            """,
        ),
        # Edge case: Not consecutive if statements - should not be transformed
        (
            """
            Int f(Bool b) {
                if (b) {
                    return 1;
                }
                Int x = 5;
                if (!b) {
                    return 1;
                }
                return 0;
            }
            """,
            """
            Int f(Bool b) {
                if (b) {
                    return 1;
                }
                Int x = 5;
                if (!b) {
                    return 1;
                }
                return 0;
            }
            """,
        ),
        # Edge case: Consecutive if statements with different behaviors - should not be transformed
        (
            """
            Int f(Bool b) {
                if (b) {
                    return 1;
                }
                if (!b) {
                    return 2;
                }
                return 0;
            }
            """,
            """
            Int f(Bool b) {
                if (b) {
                    return 1;
                }
                if (!b) {
                    return 2;
                }
                return 0;
            }
            """,
        ),
        # Edge case: Multiple exhaustive conditions with same behavior
        (
            """
            Void f(Int n) {
                if (n < 0) {
                    Int x = 1;
                }
                if (n >= 0) {
                    Int x = 1;
                }
                if (n == 5) {
                    Int x = 2;
                }
            }
            """,
            """
            Void f(Int n) {
                Int x = 1;
                if (n == 5) {
                    Int x = 2;
                }
            }
            """,
        ),
        # Edge case: Complex but exhaustive conditions with Z3 check needed
        (
            """
            Void f(Int x, Int y) {
                if (x > y) {
                    Int z = 1;
                }
                if (x <= y) {
                    Int z = 1;
                }
            }
            """,
            """
            Void f(Int x, Int y) {
                Int z = 1;
            }
            """,
        ),
        # More realistic usage: Function that handles error conditions
        # Note: Our transformer doesn't recognize these as exhaustive yet
        (
            """
            Bool validate(Int value) {
                if (value < 0) {
                    Int error = 1;
                    return false;
                }
                if (value >= 0) {
                    return true;
                }
            }
            """,
            """
            Bool validate(Int value) {
                if (value < 0) {
                    Int error = 1;
                    return false;
                }
                if (value >= 0) {
                    return true;
                }
            }
            """,
        ),
        # Case where the blocks contain variable declarations
        (
            """
            Int f(Bool condition) {
                if (condition) {
                    Int result = 42;
                    return result;
                }
                if (!condition) {
                    Int result = 42;
                    return result;
                }
                return 0;
            }
            """,
            """
            Int f(Bool condition) {
                Int result = 42;
                return result;
                return 0;
            }
            """,
        ),
    ],
)
def test_exhaustive_condition_merge(
    method: str,
    expected: str,
) -> None:
    game_ast = frog_parser.parse_method(method)
    expected_ast = frog_parser.parse_method(expected)
    
    # Create a dummy Game node to pass to the transformer
    dummy_game = frog_ast.Game(("TestGame", [], [], [game_ast], []))
    
    print("ORIGINAL: ", game_ast)
    print("EXPECTED: ", expected_ast)
    transformer = visitors.ExhaustiveConditionMergeTransformer(dummy_game)
    transformed_ast = transformer.transform(game_ast)
    print("TRANSFORMED: ", transformed_ast)
    assert expected_ast == transformed_ast 