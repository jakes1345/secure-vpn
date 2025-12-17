#ifndef DOWNLOADDIALOG_H
#define DOWNLOADDIALOG_H

#include <QDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QTableWidget>
#include <QPushButton>
#include <QLabel>
#include <QProgressBar>
#include <QHeaderView>
#include "downloadmanager.h"

class DownloadDialog : public QDialog
{
    Q_OBJECT

public:
    explicit DownloadDialog(DownloadManager *manager, QWidget *parent = nullptr);

private slots:
    void onDownloadAdded(DownloadItem *item);
    void onDownloadFinished(DownloadItem *item);
    void onDownloadProgress();
    void onPauseResume();
    void onCancel();
    void onOpenFolder();
    void onClearHistory();

private:
    void setupUI();
    void updateDownloadRow(int row, DownloadItem *item);
    int findDownloadRow(DownloadItem *item);
    
    DownloadManager *downloadManager;
    QTableWidget *downloadsTable;
    QPushButton *pauseResumeBtn;
    QPushButton *cancelBtn;
    QPushButton *openFolderBtn;
    QPushButton *clearHistoryBtn;
    QPushButton *closeBtn;
    
    QMap<DownloadItem*, int> itemToRow;
};

#endif // DOWNLOADDIALOG_H
