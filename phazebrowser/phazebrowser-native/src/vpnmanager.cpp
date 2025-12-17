#include "vpnmanager.h"
#include <QProcess>
#include <QTimer>
#include <QStandardPaths>
#include <QDir>

VPNManager::VPNManager(QObject *parent)
    : QObject(parent)
    , vpnProcess(nullptr)
    , connected(false)
{
    statusTimer = new QTimer(this);
    connect(statusTimer, &QTimer::timeout, this, &VPNManager::checkVPNStatus);
    statusTimer->start(2000); // Check every 2 seconds
    
    checkVPNStatus();
}

VPNManager::~VPNManager()
{
    if (vpnProcess) {
        vpnProcess->kill();
        vpnProcess->waitForFinished();
    }
}

bool VPNManager::isConnected() const
{
    return connected;
}

void VPNManager::connectVPN(const QString &configPath, const QString &protocol)
{
    if (vpnProcess) {
        disconnectVPN();
    }
    
    vpnProcess = new QProcess(this);
    connect(vpnProcess, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
            this, &VPNManager::onVPNProcessFinished);
    
    QStringList arguments;
    if (protocol == "openvpn") {
        vpnProcess->setProgram("openvpn");
        arguments << "--config" << configPath << "--daemon";
    } else if (protocol == "wireguard") {
        vpnProcess->setProgram("wg-quick");
        arguments << "up" << configPath;
    } else {
        return;
    }
    
    vpnProcess->setArguments(arguments);
    vpnProcess->start();
    
    // Check status after delay
    QTimer::singleShot(2000, this, &VPNManager::checkVPNStatus);
}

void VPNManager::disconnectVPN()
{
    if (vpnProcess) {
        vpnProcess->kill();
        vpnProcess->waitForFinished();
        vpnProcess->deleteLater();
        vpnProcess = nullptr;
    }
    
    // Kill any remaining VPN processes
    QProcess::execute("pkill", QStringList() << "-f" << "openvpn");
    QProcess::execute("wg-quick", QStringList() << "down" << "all");
    
    connected = false;
    vpnInterface.clear();
    stats.clear();
    
    emit statusChanged(false);
}

QVariantMap VPNManager::getStats() const
{
    return stats;
}

void VPNManager::checkVPNStatus()
{
    bool wasConnected = connected;
    connected = checkSystemVPN();
    
    if (wasConnected != connected) {
        emit statusChanged(connected);
    }
    
    if (connected) {
        // Update stats
        // TODO: Get actual stats from VPN interface
        stats["connected"] = true;
        stats["interface"] = vpnInterface;
        emit statsUpdated(stats);
    }
}

bool VPNManager::checkSystemVPN()
{
    QProcess process;
    process.start("ip", QStringList() << "link" << "show");
    process.waitForFinished();
    
    QString output = process.readAllStandardOutput();
    
    if (output.contains("tun") && output.contains("state UP")) {
        // Extract interface name
        QStringList lines = output.split('\n');
        for (const QString &line : lines) {
            if (line.contains("tun") && line.contains("state UP")) {
                QStringList parts = line.split(':');
                if (parts.size() >= 2) {
                    vpnInterface = parts[1].trimmed().split(' ').first();
                    return true;
                }
            }
        }
    }
    
    return false;
}

void VPNManager::onVPNProcessFinished(int exitCode, QProcess::ExitStatus exitStatus)
{
    Q_UNUSED(exitCode);
    Q_UNUSED(exitStatus);
    
    if (vpnProcess) {
        vpnProcess->deleteLater();
        vpnProcess = nullptr;
    }
    
    checkVPNStatus();
}
