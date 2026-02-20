import { Pagination as BootstrapPagination } from "react-bootstrap";
import type { Pagination as PaginationType } from "../../hooks/usePaginatedFetch";

interface PaginationProps {
  pagination: PaginationType;
  onPageChange: (page: number) => void;
}

export const Pagination = ({ pagination, onPageChange }: PaginationProps) => {
  const { current_page, total_pages, has_previous, has_next } = pagination;

  return (
    <BootstrapPagination>
      {/* Jump to first page */}
      <BootstrapPagination.First
        onClick={() => onPageChange(1)}
        disabled={current_page === 1}
      />

      {/* Previous page */}
      <BootstrapPagination.Prev
        onClick={() => onPageChange(current_page - 1)}
        disabled={!has_previous}
      />

      {/* Simplified pagination items, can be extended to show more page numbers */}
      <BootstrapPagination.Item active>{current_page}</BootstrapPagination.Item>

      {has_next && (
        <BootstrapPagination.Item
          onClick={() => onPageChange(current_page + 1)}
        >
          {current_page + 1}
        </BootstrapPagination.Item>
      )}
      {total_pages > current_page + 1 && <BootstrapPagination.Ellipsis />}
      {total_pages > current_page + 1 && (
        <BootstrapPagination.Item onClick={() => onPageChange(total_pages)}>
          {total_pages}
        </BootstrapPagination.Item>
      )}

      {/* Next page */}
      <BootstrapPagination.Next
        onClick={() => onPageChange(current_page + 1)}
        disabled={!has_next}
      />

      {/* Jump to last page */}
      <BootstrapPagination.Last
        onClick={() => onPageChange(total_pages)}
        disabled={current_page === total_pages}
      />
    </BootstrapPagination>
  );
};
