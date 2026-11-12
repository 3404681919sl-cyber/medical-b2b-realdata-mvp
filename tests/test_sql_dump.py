from io import StringIO

from src.sql_dump import iter_table_rows, parse_values_line


def test_parse_values_line_preserves_quoted_commas_and_converts_null():
    """Catches naive comma splitting that corrupts quoted SQL text."""
    line = "('RX-1', '2015-01-02', 'CUSTOMER, A', 'SKU-1', 2, NULL, 15.5),"

    result = parse_values_line(line)

    assert result == ["RX-1", "2015-01-02", "CUSTOMER, A", "SKU-1", "2", None, "15.5"]


def test_iter_table_rows_reads_only_requested_insert_blocks():
    """Catches rows leaking across tables or later INSERT batches being skipped."""
    dump = StringIO(
        "\n".join(
            [
                "INSERT INTO `other` (`id`) VALUES",
                "('ignore');",
                "INSERT INTO `transaction` (`id`, `qty`) VALUES",
                "('A', 1),",
                "('B', 2);",
                "INSERT INTO `other` (`id`) VALUES",
                "('ignore-2');",
                "INSERT INTO `transaction` (`id`, `qty`) VALUES",
                "('C', 3);",
            ]
        )
    )

    result = list(iter_table_rows(dump, "transaction"))

    assert result == [["A", "1"], ["B", "2"], ["C", "3"]]

