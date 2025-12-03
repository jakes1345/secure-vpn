import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Security,
  Speed,
  NetworkCheck,
  Memory,
  Storage,
  Refresh,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState({
    connections: 0,
    bandwidth: { download: 0, upload: 0 },
    latency: 0,
    cpu: 0,
    memory: 0,
    uptime: '0 days, 0 hours',
    activeUsers: 0,
    totalData: '0 GB',
  });

  const [performanceData, setPerformanceData] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Simulate real-time data updates
    const interval = setInterval(() => {
      updateStats();
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const updateStats = () => {
    // Simulate real OpenVPN statistics
    const newStats = {
      connections: Math.floor(Math.random() * 50) + 10,
      bandwidth: {
        download: Math.random() * 100 + 50,
        upload: Math.random() * 50 + 20,
      },
      latency: Math.random() * 20 + 5,
      cpu: Math.random() * 30 + 10,
      memory: Math.random() * 20 + 15,
      uptime: `${Math.floor(Math.random() * 7)} days, ${Math.floor(Math.random() * 24)} hours`,
      activeUsers: Math.floor(Math.random() * 25) + 5,
      totalData: `${(Math.random() * 100 + 50).toFixed(1)} GB`,
    };

    setStats(newStats);

    // Update performance chart data
    const timestamp = new Date().toLocaleTimeString();
    setPerformanceData(prev => {
      const newData = [...prev, {
        time: timestamp,
        download: newStats.bandwidth.download,
        upload: newStats.bandwidth.upload,
        latency: newStats.latency,
      }];
      
      // Keep only last 20 data points
      return newData.slice(-20);
    });
  };

  const getStatusColor = (value, threshold) => {
    if (value < threshold * 0.7) return 'success';
    if (value < threshold * 0.9) return 'warning';
    return 'error';
  };

  const StatCard = ({ title, value, icon, color, subtitle, progress }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h6" color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div" color={color}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box color={color}>
            {icon}
          </Box>
        </Box>
        {progress && (
          <Box mt={2}>
            <LinearProgress
              variant="determinate"
              value={progress}
              color={getStatusColor(progress, 100)}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          SecureVPN Dashboard
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Chip
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            icon={<Security />}
          />
          <Tooltip title="Refresh">
            <IconButton onClick={updateStats}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Connection Status */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="Active Connections"
            value={stats.connections}
            icon={<NetworkCheck fontSize="large" />}
            color="primary.main"
            subtitle="OpenVPN clients"
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="Download Speed"
            value={`${stats.bandwidth.download.toFixed(1)} Mbps`}
            icon={<Speed fontSize="large" />}
            color="success.main"
            subtitle="Current bandwidth"
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="Upload Speed"
            value={`${stats.bandwidth.upload.toFixed(1)} Mbps`}
            icon={<Speed fontSize="large" />}
            color="info.main"
            subtitle="Current bandwidth"
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="Latency"
            value={`${stats.latency.toFixed(1)} ms`}
            icon={<NetworkCheck fontSize="large" />}
            color="warning.main"
            subtitle="Average ping"
          />
        </Grid>
      </Grid>

      {/* System Resources */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="CPU Usage"
            value={`${stats.cpu.toFixed(1)}%`}
            icon={<Memory fontSize="large" />}
            color="secondary.main"
            progress={stats.cpu}
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="Memory Usage"
            value={`${stats.memory.toFixed(1)}%`}
            icon={<Storage fontSize="large" />}
            color="secondary.main"
            progress={stats.memory}
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="Server Uptime"
            value={stats.uptime}
            icon={<Security fontSize="large" />}
            color="success.main"
            subtitle="Continuous operation"
          />
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <StatCard
            title="Total Data"
            value={stats.totalData}
            icon={<Storage fontSize="large" />}
            color="info.main"
            subtitle="Transferred today"
          />
        </Grid>
      </Grid>

      {/* Performance Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Network Performance
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line
                    type="monotone"
                    dataKey="download"
                    stroke="#4caf50"
                    strokeWidth={2}
                    name="Download (Mbps)"
                  />
                  <Line
                    type="monotone"
                    dataKey="upload"
                    stroke="#2196f3"
                    strokeWidth={2}
                    name="Upload (Mbps)"
                  />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="#ff9800"
                    strokeWidth={2}
                    name="Latency (ms)"
                    yAxisId={1}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Security Status
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">AES-256-GCM Encryption</Typography>
                  <Chip label="Active" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">SSL Certificate</Typography>
                  <Chip label="Valid" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Firewall Rules</Typography>
                  <Chip label="Active" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">DNS Protection</Typography>
                  <Chip label="Active" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Kill Switch</Typography>
                  <Chip label="Enabled" color="success" size="small" />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Traffic Obfuscation</Typography>
                  <Chip label="Active" color="success" size="small" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Grid container spacing={3} mt={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Chip
                  label="Generate Client Config"
                  color="primary"
                  variant="outlined"
                  clickable
                />
                <Chip
                  label="View Logs"
                  color="secondary"
                  variant="outlined"
                  clickable
                />
                <Chip
                  label="Restart Server"
                  color="warning"
                  variant="outlined"
                  clickable
                />
                <Chip
                  label="Backup Configuration"
                  color="info"
                  variant="outlined"
                  clickable
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
