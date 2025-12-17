#include "devtools.h"
#include "browserwindow.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QLabel>
#include <QSplitter>
#include <QHeaderView>

DevTools::DevTools(BrowserWindow *browser, QWidget *parent)
    : QDockWidget("Developer Tools", parent)
    , m_browser(browser)
{
    setAllowedAreas(Qt::BottomDockWidgetArea | Qt::RightDockWidgetArea);
    setupUI();
}

void DevTools::setupUI()
{
    m_tabs = new QTabWidget(this);
    setWidget(m_tabs);
    
    setupConsole();
    setupNetwork();
    setupElements();
    setupApplication();
    setupSecurity();
}

void DevTools::setupConsole()
{
    QWidget *consoleWidget = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(consoleWidget);
    
    m_console = new QTextEdit();
    m_console->setReadOnly(true);
    m_console->setFont(QFont("Monospace", 10));
    m_console->setStyleSheet("background: #1e1e1e; color: #d4d4d4;");
    
    layout->addWidget(m_console);
    
    m_tabs->addTab(consoleWidget, "Console");
}

void DevTools::setupNetwork()
{
    QWidget *networkWidget = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(networkWidget);
    
    m_networkTable = new QTableWidget();
    m_networkTable->setColumnCount(5);
    m_networkTable->setHorizontalHeaderLabels(QStringList() << "Method" << "URL" << "Status" << "Type" << "Size");
    m_networkTable->horizontalHeader()->setStretchLastSection(true);
    m_networkTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    
    layout->addWidget(m_networkTable);
    
    m_tabs->addTab(networkWidget, "Network");
}

void DevTools::setupElements()
{
    QWidget *elementsWidget = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(elementsWidget);
    
    m_elementsTree = new QTreeWidget();
    m_elementsTree->setHeaderLabel("DOM Elements");
    m_elementsTree->setStyleSheet("background: #1e1e1e; color: #d4d4d4;");
    
    layout->addWidget(m_elementsTree);
    
    m_tabs->addTab(elementsWidget, "Elements");
}

void DevTools::setupApplication()
{
    QWidget *appWidget = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(appWidget);
    
    m_applicationTree = new QTreeWidget();
    m_applicationTree->setHeaderLabel("Application Storage");
    m_applicationTree->setStyleSheet("background: #1e1e1e; color: #d4d4d4;");
    
    layout->addWidget(m_applicationTree);
    
    m_tabs->addTab(appWidget, "Application");
}

void DevTools::setupSecurity()
{
    QWidget *securityWidget = new QWidget();
    QVBoxLayout *layout = new QVBoxLayout(securityWidget);
    
    m_securityInfo = new QTextEdit();
    m_securityInfo->setReadOnly(true);
    m_securityInfo->setStyleSheet("background: #1e1e1e; color: #d4d4d4;");
    
    layout->addWidget(m_securityInfo);
    
    m_tabs->addTab(securityWidget, "Security");
}

void DevTools::showConsole()
{
    m_tabs->setCurrentIndex(0);
    show();
    raise();
}

void DevTools::showNetwork()
{
    m_tabs->setCurrentIndex(1);
    show();
    raise();
}

void DevTools::showElements()
{
    m_tabs->setCurrentIndex(2);
    show();
    raise();
}

void DevTools::showApplication()
{
    m_tabs->setCurrentIndex(3);
    show();
    raise();
}

void DevTools::showSecurity()
{
    m_tabs->setCurrentIndex(4);
    show();
    raise();
}

void DevTools::showPageSource()
{
    if (!m_pageSource) {
        QWidget *sourceWidget = new QWidget();
        QVBoxLayout *layout = new QVBoxLayout(sourceWidget);
        
        m_pageSource = new QTextEdit();
        m_pageSource->setReadOnly(true);
        m_pageSource->setFont(QFont("Monospace", 10));
        m_pageSource->setStyleSheet("background: #1e1e1e; color: #d4d4d4;");
        
        layout->addWidget(m_pageSource);
        
        m_tabs->addTab(sourceWidget, "Page Source");
    }
    
    // Get page source
    if (m_browser) {
        m_browser->webView()->page()->toHtml([this](const QString &html) {
            if (m_pageSource) {
                m_pageSource->setPlainText(html);
            }
        });
    }
    
    m_tabs->setCurrentIndex(m_tabs->count() - 1);
    show();
    raise();
}

void DevTools::onConsoleMessage(const QString &message, int line, const QString &source)
{
    Q_UNUSED(line);
    Q_UNUSED(source);
    m_console->append(message);
}

void DevTools::onNetworkRequest(const QUrl &url, const QString &method)
{
    int row = m_networkTable->rowCount();
    m_networkTable->insertRow(row);
    m_networkTable->setItem(row, 0, new QTableWidgetItem(method));
    m_networkTable->setItem(row, 1, new QTableWidgetItem(url.toString()));
    m_networkTable->setItem(row, 2, new QTableWidgetItem("Pending"));
    m_networkTable->setItem(row, 3, new QTableWidgetItem(""));
    m_networkTable->setItem(row, 4, new QTableWidgetItem(""));
}

void DevTools::onNetworkResponse(const QUrl &url, int status, const QString &contentType)
{
    for (int i = 0; i < m_networkTable->rowCount(); i++) {
        if (m_networkTable->item(i, 1)->text() == url.toString()) {
            m_networkTable->setItem(i, 2, new QTableWidgetItem(QString::number(status)));
            m_networkTable->setItem(i, 3, new QTableWidgetItem(contentType));
            break;
        }
    }
}
