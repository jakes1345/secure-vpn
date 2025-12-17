#ifndef PRIVACYENGINE_H
#define PRIVACYENGINE_H

#include <QObject>
#include <QWebEngineView>
#include <QWebEngineProfile>
#include <QWebEngineSettings>
#include <QString>
#include <QStringList>
#include <QSet>
#include <QJsonObject>

class PrivacyEngine : public QObject
{
    Q_OBJECT

public:
    explicit PrivacyEngine(QObject *parent = nullptr);
    
    void applyPrivacySettings(QWebEngineView *webView);
    void injectAdBlocking(QWebEngineView *webView);
    void injectTrackingProtection(QWebEngineView *webView);
    void injectFingerprintProtection(QWebEngineView *webView);
    void injectCookieBlocking(QWebEngineView *webView);
    
    // Settings
    void setAdBlocking(bool enabled);
    void setTrackingProtection(bool enabled);
    void setFingerprintProtection(bool enabled);
    void setCookieBlocking(bool enabled);
    void setBlockAllCookies(bool enabled);
    void setBlockFonts(bool enabled);
    void setBlockCamera(bool enabled);
    void setBlockMicrophone(bool enabled);
    void setBlockGeolocation(bool enabled);
    void setBlockNotifications(bool enabled);
    
    // Stats
    QJsonObject getPrivacyStats() const;
    void resetStats();

private:
    QString getAdBlockingJS();
    QString getTrackingProtectionJS();
    QString getFingerprintProtectionJS();
    QString getCookieBlockingJS();
    QString getFontBlockingCSS();
    
    // Settings
    bool m_adBlocking;
    bool m_trackingProtection;
    bool m_fingerprintProtection;
    bool m_cookieBlocking;
    bool m_blockAllCookies;
    bool m_blockFonts;
    bool m_blockCamera;
    bool m_blockMicrophone;
    bool m_blockGeolocation;
    bool m_blockNotifications;
    
    // Stats
    int m_adsBlocked;
    int m_trackersBlocked;
    int m_cookiesBlocked;
    int m_requestsBlocked;
    QSet<QString> m_domainsBlocked;
    
    // Filter lists
    QStringList m_blockedDomains;
    QStringList m_adPatterns;
    QStringList m_trackingDomains;
};

#endif // PRIVACYENGINE_H
