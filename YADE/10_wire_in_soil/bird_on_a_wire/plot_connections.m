clearvars
close all
clc;

if ~exist('output_postprocess','dir')
mkdir('output_postprocess')
mkdir('imported_data')
end
    if isfile(['imported_data/data_mat.mat'])
    
        load(['imported_data/data_mat.mat'])
        disp('Reloaded data')
    else
        
        disp('nodes.txt is loading')
d = ff_import_txt('nodes.txt');

% t id1 id2 x y z bendx y z twist x y z normal x y z shear x y z
disp('Connection.txt is loading')
dc = ff_import_txt('connections.txt');
dc = 

% t id rad x y z vx vy vz spinx y z
disp('balls.txt is loading')
bd = ff_import_txt('balls.txt');

% t id0 id1 id2 x y z bendx y z twistx y z forcex y z shear x y z
disp('wire.txt is loading')
wd = ff_import_txt('wire.txt');
        
      

    save(['imported_data/data_mat.mat'],'d','dc','bd','wd','','-mat','-v7.3');   
    
    end
        disp('Imported all data, starting postprocessing procedure.')
        
        

%%
t = unique(dc(:,1));
t0 = t(1);

tw = unique(wd(:,1));

%t = t-t0;
vec_disp = nan(length(t),1);
mat_force = nan(length(t),3);

nn = min([length(t),length(tw)]);
for tidx = 1:nn-1
    
    % contacts at t
    ic = dc(:,1)==t(tidx);
    lc = dc(ic,:);
    
    % wire elements at t
    id = d(:,1)==t(tidx);
    ld = d(id,:);

    % wire interactions at t
    iw = wd(:,1)==tw(tidx);
    lw = wd(iw,:);
    

%         % balls at t
%     ib = bd(:,1)==t(tidx);
%     lb = bd(ib,:);
    

idx_conns_wire = find(or(lc(:,2)<21,lc(:,3)<211));


    myDisp = max(abs(3-ld(:,3)));
    
    
    figure(10)
    subplot(1,3,1)
    plot(ld(:,3));
    subplot(1,3,2)
    plot(ld(:,4));
    subplot(1,3,3)
    plot(ld(:,5));
    drawnow
    vec_disp(tidx)=myDisp;
    
    figure(11)
    plot3(ld(:,3),ld(:,4),ld(:,5),'k-','LineWidth',2)
    axis equal
    %myForce = sum(lc(idx_conns_wire,13:15));
    
    myForce = sum(lw(:,14:16));
    
    mat_force(tidx,:)=myForce;
    
    

    


end

xlabel('x [m]');
ylabel('y [m]');
zlabel('z [m]');

print('deformata.png','-dpng','-r1200');

figure
plot(t,vec_disp);
xlabel('Time [s]');
ylabel('Displacement [m]');
print('time deform.png','-dpng','-r1200');


figure
xyz = {'x','z'};
subplot(1,2,1);
plot(t,mat_force(:,1));
xlabel('Time [s]');
ylabel('Force along X [N]');
subplot(1,2,2);
plot(t,mat_force(:,3));
xlabel('Time [s]');
ylabel('Force along Z [N]');
print('time forces.png','-dpng','-r1200');

