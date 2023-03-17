%  close all
%  clearvars
% 
% 
% load("py_pedone_SNW_drained_putty_ascii_mesh_data.mat");
% load("py_pedone_SNW_drained_putty_ascii_results.mat");

vel = 0.001;
steps = [myResults.Time]';

displacements = steps * vel;
%%

for tidx = 1:length(steps)

mm = myMesh(tidx).Nodes;


% 1 id, x y z , modulus
CFORCE = myResults(tidx).CONTACT_FORCE;


el = myMesh(tidx).Kratos_Triangle2D3_Mesh_2;
el = reshape(el(:,2:4),numel(el(:,2:4)),1);
el = unique(el);

%plot(mm(:,2),mm(:,3),'.')
% hold on
% plot(mm(:,2),mm(:,3),'k.')
% plot(mm(el,2),mm(el,3),'r.')
% quiver(mm(el,2),mm(el,3),CFORCE(el,2),CFORCE(el,3))

myF = sum(CFORCE(el,3));

vec_F(tidx)=myF;

end



close all
plot(displacements,vec_F)