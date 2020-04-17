
/*
 * Show FAT partition info and list files.
 */

#include "FFat.h"
#include "esp_partition.h"


void listDir(fs::FS &fs, const char * dirname, uint8_t level) {

  Serial.printf("Listing directory: %s\r\n", dirname);

  File root = fs.open(dirname);
  if (!root) {
    Serial.println("- failed to open directory");
    return;
  }
  if (!root.isDirectory()) {
    Serial.println(" - not a directory");
    return;
  }

  File file = root.openNextFile();
  while (file) {
    if (strstr(file.name(), "/.") == 0) {      
      for (int i=0;i<level;i++)
        Serial.print("  ");
      if (file.isDirectory()) {
        Serial.print("DIR : ");
        Serial.println(file.name());
        listDir(fs, file.name(), level+1);
      } else {
          Serial.print("SIZE: ");
          Serial.print(file.size());
          Serial.print("  \tFILE: ");
          Serial.println(&file.name()[strlen(dirname)+level]);
      }
    }
    file = root.openNextFile();
  }
}


void setup() {
  Serial.begin(115200);
  Serial.println();
  if(!FFat.begin(false)){
    Serial.println("Mount Failed");
    return;
  }  
  Serial.println("File system mounted");
  Serial.println();
 
  const esp_partition_t *p = esp_partition_find_first(ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_DATA_FAT, NULL);

  Serial.printf("Partition label: %s\n", p->label);
  Serial.printf("Partition start: %08lx\n", p->address);
  Serial.printf("Partition size : %08lx\n\n\n", p->size);

  listDir(FFat, "/", 0);
}

void loop() {}
