package com.phazevpn.client

import android.content.Intent
import android.net.VpnService
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.textview.MaterialTextView
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    
    private lateinit var connectButton: MaterialButton
    private lateinit var statusText: MaterialTextView
    private lateinit var ipText: MaterialTextView
    private lateinit var vpnIpText: MaterialTextView
    private lateinit var downloadText: MaterialTextView
    private lateinit var uploadText: MaterialTextView
    private lateinit var durationText: MaterialTextView
    
    private var isConnected = false
    private val VPN_REQUEST_CODE = 1001
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        initViews()
        setupListeners()
        updateUI()
    }
    
    private fun initViews() {
        connectButton = findViewById(R.id.connectButton)
        statusText = findViewById(R.id.statusText)
        ipText = findViewById(R.id.ipText)
        vpnIpText = findViewById(R.id.vpnIpText)
        downloadText = findViewById(R.id.downloadText)
        uploadText = findViewById(R.id.uploadText)
        durationText = findViewById(R.id.durationText)
    }
    
    private fun setupListeners() {
        connectButton.setOnClickListener {
            if (isConnected) {
                disconnect()
            } else {
                requestVpnPermission()
            }
        }
    }
    
    private fun requestVpnPermission() {
        val intent = VpnService.prepare(this)
        if (intent != null) {
            startActivityForResult(intent, VPN_REQUEST_CODE)
        } else {
            onActivityResult(VPN_REQUEST_CODE, RESULT_OK, null)
        }
    }
    
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == VPN_REQUEST_CODE && resultCode == RESULT_OK) {
            connect()
        } else {
            Toast.makeText(this, "VPN permission denied", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun connect() {
        // Start VPN service
        val intent = Intent(this, com.phazevpn.client.VpnService::class.java)
        intent.action = "CONNECT"
        startService(intent)
        
        isConnected = true
        updateUI()
        
        // Simulate connection process
        lifecycleScope.launch {
            statusText.text = "Connecting..."
            delay(1000)
            statusText.text = "Handshaking..."
            delay(1000)
            statusText.text = "Connected • Secured"
            vpnIpText.text = "VPN IP: 10.9.0.${(2..254).random()}"
            
            // Start stats update loop
            startStatsUpdate()
        }
    }
    
    private fun disconnect() {
        // Stop VPN service
        val intent = Intent(this, com.phazevpn.client.VpnService::class.java)
        stopService(intent)
        
        isConnected = false
        updateUI()
        
        statusText.text = "Disconnected"
        vpnIpText.text = "VPN IP: Not Connected"
        durationText.text = "Duration: 00:00:00"
    }
    
    private fun updateUI() {
        if (isConnected) {
            connectButton.text = "🔌 DISCONNECT"
            connectButton.setBackgroundColor(getColor(android.R.color.holo_red_dark))
        } else {
            connectButton.text = "⚡ CONNECT"
            connectButton.setBackgroundColor(getColor(android.R.color.holo_blue_dark))
        }
    }
    
    private fun startStatsUpdate() {
        lifecycleScope.launch {
            var seconds = 0
            while (isConnected) {
                delay(1000)
                seconds++
                
                val hours = seconds / 3600
                val minutes = (seconds % 3600) / 60
                val secs = seconds % 60
                
                durationText.text = String.format("Duration: %02d:%02d:%02d", hours, minutes, secs)
                
                // Simulate bandwidth (random for demo)
                val download = (Math.random() * 10).toInt()
                val upload = (Math.random() * 5).toInt()
                downloadText.text = "↓ ${download}.${(Math.random() * 10).toInt()} MB"
                uploadText.text = "↑ ${upload}.${(Math.random() * 10).toInt()} MB"
            }
        }
    }
}
