#
# Generated Makefile - do not edit!
#
# Edit the Makefile in the project folder instead (../Makefile). Each target
# has a -pre and a -post target defined where you can add customized code.
#
# This makefile implements configuration specific macros and targets.


# Environment
MKDIR=mkdir
CP=cp
GREP=grep
NM=nm
CCADMIN=CCadmin
RANLIB=ranlib
CC=gcc
CCC=g++
CXX=g++
FC=g++
AS=as

# Macros
CND_PLATFORM=GNU_SUDO_GDB-Linux-x86
CND_DLIB_EXT=so
CND_CONF=Debug
CND_DISTDIR=dist
CND_BUILDDIR=build

# Include project Makefile
include Makefile

# Object Directory
OBJECTDIR=${CND_BUILDDIR}/${CND_CONF}/${CND_PLATFORM}

# Object Files
OBJECTFILES= \
	${OBJECTDIR}/src/arpInfo.o \
	${OBJECTDIR}/src/associations.o \
	${OBJECTDIR}/src/graphClient.o


# C Compiler Flags
CFLAGS=-D__GIT_VERSION=\"$(GIT_VERSION)\"

# CC Compiler Flags
CCFLAGS=
CXXFLAGS=

# Fortran Compiler Flags
FFLAGS=

# Assembler Flags
ASFLAGS=

# Link Libraries and Options
LDLIBSOPTIONS=`pkg-config --libs libnl-3.0 libnl-genl-3.0`  

# Build Targets
.build-conf: ${BUILD_SUBPROJECTS}
	"${MAKE}"  -f nbproject/Makefile-${CND_CONF}.mk ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/graphclient

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/graphclient: ${OBJECTFILES}
	${MKDIR} -p ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}
	${LINK.c} -o ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/graphclient ${OBJECTFILES} ${LDLIBSOPTIONS}

${OBJECTDIR}/src/arpInfo.o: src/arpInfo.c 
	${MKDIR} -p ${OBJECTDIR}/src
	${RM} $@.d
	$(COMPILE.c) -g `pkg-config --cflags libnl-3.0 libnl-genl-3.0` -MMD -MP -MF $@.d -o ${OBJECTDIR}/src/arpInfo.o src/arpInfo.c

${OBJECTDIR}/src/associations.o: src/associations.c 
	${MKDIR} -p ${OBJECTDIR}/src
	${RM} $@.d
	$(COMPILE.c) -g `pkg-config --cflags libnl-3.0 libnl-genl-3.0` -MMD -MP -MF $@.d -o ${OBJECTDIR}/src/associations.o src/associations.c

${OBJECTDIR}/src/graphClient.o: src/graphClient.c 
	${MKDIR} -p ${OBJECTDIR}/src
	${RM} $@.d
	$(COMPILE.c) -g `pkg-config --cflags libnl-3.0 libnl-genl-3.0` -MMD -MP -MF $@.d -o ${OBJECTDIR}/src/graphClient.o src/graphClient.c

# Subprojects
.build-subprojects:

# Clean Targets
.clean-conf: ${CLEAN_SUBPROJECTS}
	${RM} -r ${CND_BUILDDIR}/${CND_CONF}
	${RM} ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/graphclient

# Subprojects
.clean-subprojects:

# Enable dependency checking
.dep.inc: .depcheck-impl

include .dep.inc
