#pragma once

#include "base/src/export.h"

#ifdef CONTACTMODEL_LIB
# define CONTACTMODEL_EXPORT EXPORT_TAG
#else
# define CONTACTMODEL_EXPORT IMPORT_TAG
#endif

// EoF
