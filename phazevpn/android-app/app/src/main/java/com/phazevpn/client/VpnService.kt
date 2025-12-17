package com.phazevpn.client

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import androidx.core.app.NotificationCompat
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.InetSocketAddress
import java.nio.ByteBuffer
import java.nio.channels.DatagramChannel

class VpnService : VpnService() {
    
    private var vpnInterface: ParcelFileDescriptor? = null
    private var isRunning = false
    private val SERVER_HOST = "15.204.11.19"
    private val SERVER_PORT = 51820
    
    companion object {
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "phazevpn_channel"
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "CONNECT") {
            startVpn()
        } else {
            stopVpn()
        }
        return START_STICKY
    }
    
    private fun startVpn() {
        if (isRunning) return
        
        try {
            // Create VPN interface
            val builder = Builder()
            builder.setSession("PhazeVPN")
            builder.addAddress("10.9.0.${(2..254).random()}", 24)
            builder.addRoute("0.0.0.0", 0)
            builder.addDnsServer("1.1.1.1")
            builder.setMtu(1500)
            
            vpnInterface = builder.establish()
            isRunning = true
            
            // Start foreground service with notification
            startForeground(NOTIFICATION_ID, createNotification("Connected"))
            
            // Start VPN tunnel in background thread
            Thread {
                runVpnTunnel()
            }.start()
            
        } catch (e: Exception) {
            e.printStackTrace()
            stopVpn()
        }
    }
    
    private fun runVpnTunnel() {
        try {
            val inputStream = FileInputStream(vpnInterface?.fileDescriptor)
            val outputStream = FileOutputStream(vpnInterface?.fileDescriptor)
            
            // Connect to VPN server
            val serverChannel = DatagramChannel.open()
            serverChannel.connect(InetSocketAddress(SERVER_HOST, SERVER_PORT))
            
            val packet = ByteBuffer.allocate(32767)
            
            while (isRunning) {
                // Read from TUN interface
                packet.clear()
                val length = inputStream.read(packet.array())
                if (length > 0) {
                    // Send to VPN server (encrypted in production)
                    packet.limit(length)
                    serverChannel.write(packet)
                }
                
                // Read from VPN server
                packet.clear()
                serverChannel.read(packet)
                if (packet.position() > 0) {
                    // Write to TUN interface
                    outputStream.write(packet.array(), 0, packet.position())
                }
            }
            
            serverChannel.close()
            inputStream.close()
            outputStream.close()
            
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun stopVpn() {
        isRunning = false
        vpnInterface?.close()
        vpnInterface = null
        stopForeground(true)
        stopSelf()
    }
    
    private fun createNotification(message: String): android.app.Notification {
        createNotificationChannel()
        
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("PhazeVPN")
            .setContentText(message)
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "PhazeVPN Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        stopVpn()
    }
}
