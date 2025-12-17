#ifndef SEARCHMANAGER_H
#define SEARCHMANAGER_H

#include <QObject>
#include <QJsonArray>
#include <QJsonObject>
#include <QString>
#include <QUrl>

class SearchEngine
{
public:
    QString name;
    QString keyword;
    QString url;
    bool isDefault;
    
    SearchEngine() : isDefault(false) {}
    SearchEngine(const QString &n, const QString &k, const QString &u, bool def = false)
        : name(n), keyword(k), url(u), isDefault(def) {}
    
    QUrl searchUrl(const QString &query) const;
};

class SearchManager : public QObject
{
    Q_OBJECT

public:
    explicit SearchManager(QObject *parent = nullptr);
    
    QList<SearchEngine> searchEngines() const;
    SearchEngine defaultEngine() const;
    void setDefaultEngine(const QString &keyword);
    
    void addEngine(const SearchEngine &engine);
    void removeEngine(const QString &keyword);
    void updateEngine(const QString &keyword, const SearchEngine &engine);
    
    QUrl searchUrl(const QString &query, const QString &engineKeyword = QString()) const;
    QStringList suggestions(const QString &query) const;

private:
    QList<SearchEngine> m_engines;
    QString m_defaultKeyword;
    
    void loadEngines();
    void saveEngines();
    QString getEnginesPath() const;
};

#endif // SEARCHMANAGER_H
