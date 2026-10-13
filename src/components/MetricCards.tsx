import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  status?: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  colorBorder?: string;
  icon?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  status = 'neutral',
  colorBorder,
  icon,
}) => {
  const getStatusClasses = () => {
    switch (status) {
      case 'success':
        return 'text-[#178A5B] bg-[#EDF9F0] border-[#B8E6CB]';
      case 'warning':
        return 'text-[#D48A00] bg-[#FFFBEA] border-[#FCE5B2]';
      case 'danger':
        return 'text-[#D92D20] bg-[#FEF3F2] border-[#FECDCA]';
      case 'info':
        return 'text-[#0B4EA2] bg-[#EAF3FF] border-[#B3D4FF]';
      default:
        return 'text-[#172B4D] bg-white border-[#DCE3EA]';
    }
  };

  return (
    <div
      className="p-4 rounded-xl border bg-white shadow-xs flex flex-col justify-between transition-all hover:shadow-md"
      style={colorBorder ? { borderTop: `3px solid ${colorBorder}` } : {}}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-[#5E6C84] tracking-tight">{label}</span>
        {icon && <span className="text-base">{icon}</span>}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-extrabold tracking-tight text-[#172B4D]">{value}</span>
      </div>
      {subValue && (
        <div className="mt-2 text-xs font-medium text-[#5E6C84]">
          {subValue}
        </div>
      )}
    </div>
  );
};
