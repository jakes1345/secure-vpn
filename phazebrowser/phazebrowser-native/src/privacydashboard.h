#ifndef PRIVACYDASHBOARD_H
#define PRIVACYDASHBOARD_H

#include <QDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QTableWidget>
#include <QPushButton>
#include <QGroupBox>
#include <QProgressBar>
#include "privacyengine.h"

class PrivacyDashboard : public QDialog
{
    Q_OBJECT

public:
    explicit PrivacyDashboard(PrivacyEngine *privacyEngine, QWidget *parent = nullptr);

private slots:
    void updateStats();
    void onResetStats();

private:
    void setupUI();
    
    PrivacyEngine *privacyEngine;
    
    // Stats labels
    QLabel *adsBlockedLabel;
    QLabel *trackersBlockedLabel;
    QLabel *cookiesBlockedLabel;
    QLabel *requestsBlockedLabel;
    QLabel *domainsBlockedLabel;
    
    // Protection status
    QLabel *adBlockingStatus;
    QLabel *trackingProtectionStatus;
    QLabel *fingerprintProtectionStatus;
    QLabel *cookieBlockingStatus;
    
    // Blocked domains table
    QTableWidget *domainsTable;
    
    QTimer *updateTimer;
};

#endif // PRIVACYDASHBOARD_H
