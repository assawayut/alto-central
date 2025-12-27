interface BarGaugeProps {
  labels: string[];
  colors: string[];
  value: number;
  threshold: number[]; // Should have length of colors.length + 1
  showValue?: boolean;
}

export function BarGauge({ labels, colors, value, threshold, showValue = true }: BarGaugeProps) {
  // Calculate percentage based on linear interpolation between thresholds
  const minThreshold = threshold[0];
  const maxThreshold = threshold[threshold.length - 1];
  const percentage = Math.min(Math.max(((value - minThreshold) / (maxThreshold - minThreshold)) * 100, 0), 100);

  // Get the current section color
  const currentLevel = threshold.slice(0, -1).findIndex((t) => value <= t);
  const currentColor = currentLevel !== -1 ? colors[currentLevel - 1] : colors[colors.length - 1];

  // Calculate section widths based on thresholds
  const sectionWidths = colors.map((_, i) => {
    const start = threshold[i];
    const end = threshold[i + 1];
    return ((end - start) / (maxThreshold - minThreshold)) * 100;
  });

  // Clamp the position to prevent text overflow
  const clampedLeft = Math.max(10, Math.min(90, percentage));

  // Calculate tick positions (cumulative percentage for each threshold), with clamping
  const tickPositions = threshold.map((t) => {
    const pos = ((t - minThreshold) / (maxThreshold - minThreshold)) * 100;
    return Math.max(2, Math.min(98, pos)); // Adjusted clamping for tighter fit
  });

  return (
    <div className="relative w-full max-w-full mb-2"> {/* Ensure it doesn’t exceed parent */}
      {/* Value display */}
      {showValue && (
        <div
          className="absolute -top-8 transform -translate-x-1/2"
          style={{
            left: `${clampedLeft}%`,
            minWidth: "0",
            whiteSpace: "nowrap",
          }}
        >
          <div className="text-xl font-semibold" style={{ color: currentColor }}>
            {value == null ? '-' : value.toFixed(3)}
          </div>
        </div>
      )}

      {/* Triangle indicator */}
      {showValue && (
        <div
          className="absolute -top-2 transform -translate-x-1/2 transition-all duration-300"
          style={{ left: `${percentage}%` }}
        >
          <div
            className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px]"
            style={{ borderTopColor: currentColor }}
          />
        </div>
      )}

      {/* Bar sections */}
      <div className="flex h-5 rounded-md overflow-hidden">
        {colors.map((color, index) => (
          <div
            key={index}
            className="flex items-center justify-center text-[10px] text-white font-semibold"
            style={{
              backgroundColor: color,
              width: `${sectionWidths[index]}%`,
            }}
          >
            {labels[index]}
          </div>
        ))}
      </div>

      {/* Tick labels */}
      <div className="relative w-full mt-0 flex justify-between">
        {threshold.map((tickValue, index) => (
          <div
            key={index}
            className="absolute text-[10px] text-gray-600 font-normal transform -translate-x-1/2"
            style={{
              left: `${tickPositions[index]}%`,
              maxWidth: "100%", // Prevent text from extending too far
              whiteSpace: "nowrap", // Keep text on one line
              // Add padding to prevent clipping at edges
              paddingLeft: index === 0 ? "2px" : "0", // Small left padding for first tick
              paddingRight: index === threshold.length - 1 ? "2px" : "0", // Small right padding for last tick
            }}
          >
            {tickValue.toLocaleString(undefined,{
              maximumFractionDigits:2,
              minimumFractionDigits:1
            })}
          </div>
        ))}
      </div>
    </div>
  );
}