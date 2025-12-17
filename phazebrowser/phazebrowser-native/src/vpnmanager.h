#ifndef VPNMANAGER_H
#define VPNMANAGER_H

#include <QObject>
#include <QProcess>
#include <QTimer>
#include <QVariantMap>

class VPNManager : public QObject
{
    Q_OBJECT

public:
    explicit VPNManager(QObject *parent = nullptr);
    ~VPNManager();
    
    bool isConnected() const;
    void connectVPN(const QString &configPath, const QString &protocol);
    void disconnectVPN();
    QVariantMap getStats() const;

signals:
    void statusChanged(bool connected);
    void statsUpdated(const QVariantMap &stats);

private slots:
    void checkVPNStatus();
    void onVPNProcessFinished(int exitCode, QProcess::ExitStatus exitStatus);

private:
    QProcess *vpnProcess;
    QTimer *statusTimer;
    bool connected;
    QString vpnInterface;
    QVariantMap stats;
    
    bool checkSystemVPN();
};

#endif // VPNMANAGER_H
