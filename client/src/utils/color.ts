export const getClusterColor = (clusterId: number, alpha: number = 0.2) => {
  // Handle noise
  if (clusterId === -1) {
    return `rgba(158, 158, 158, ${alpha})`;
  }

  // clusterId -> hue
  // This is some hack involving the "golden angle"
  const hue = (clusterId * 137.508) % 360;

  // Apparently, (Saturation 70%, Lightness 50% are good for highlights)
  return `hsla(${hue}, 70%, 50%, ${alpha})`;
};
