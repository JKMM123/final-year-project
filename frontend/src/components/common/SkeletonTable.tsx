import { Table, Placeholder } from "react-bootstrap";

interface SkeletonTableProps {
  rows?: number;
  cols?: number;
}

export const SkeletonTable = ({ rows = 5, cols = 4 }: SkeletonTableProps) => {
  return (
    <Table responsive striped>
      <thead>
        <tr>
          {Array.from({ length: cols }).map((_, index) => (
            <th key={index}>
              <Placeholder as="div" animation="glow">
                <Placeholder xs={12} />
              </Placeholder>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <tr key={rowIndex}>
            {Array.from({ length: cols }).map((_, colIndex) => (
              <td key={colIndex}>
                <Placeholder as="div" animation="glow">
                  <Placeholder xs={12} />
                </Placeholder>
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </Table>
  );
};
