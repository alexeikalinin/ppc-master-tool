"use client";

interface Column<T> {
  key: keyof T;
  label: string;
  render?: (val: T[keyof T], row: T) => React.ReactNode;
}

interface ResultsTableProps<T extends object> {
  columns: Column<T>[];
  data: T[];
  className?: string;
}

export default function ResultsTable<T extends object>({
  columns,
  data,
  className = "",
}: ResultsTableProps<T>) {
  if (!data.length) {
    return <p className="text-gray-500 text-lg py-6 text-center">Нет данных</p>;
  }

  return (
    <div className={`overflow-x-auto rounded-xl border border-white/10 ${className}`}>
      <table className="w-full text-base">
        <thead>
          <tr className="border-b border-white/10 bg-white/[0.03]">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className="text-left px-5 py-4 text-gray-400 text-sm font-semibold uppercase tracking-widest whitespace-nowrap"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className={`border-b border-white/5 transition-colors hover:bg-indigo-500/5 ${
                i % 2 === 1 ? "bg-white/[0.02]" : ""
              }`}
            >
              {columns.map((col) => (
                <td key={String(col.key)} className="px-5 py-4 text-gray-200 text-base">
                  {col.render
                    ? col.render(row[col.key], row)
                    : String(row[col.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
